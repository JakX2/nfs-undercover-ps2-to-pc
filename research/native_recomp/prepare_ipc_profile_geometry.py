#!/usr/bin/env python3
"""Authenticate the next original IPC profiling helper, without exporting guest data."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_private_elf_symbol_map import HEADER, SECTION, SYMBOL, ORIGINAL_SHA256, parse_functions
from prepare_v419_full_start import MAX_DOL, OWNER_SHA, direct_bl
from make_v624_ipc_geometry import exact_words
from make_start_to_ipc_submit_v72 import EDGES

OBJECTS=(b'IpcNumPendingReqs',b'IpcNumUnIssuedReqs',b'IpcReqPtrArray',b'IpcFdArray')
CALL,HELPER=EDGES[3]

def layout(dol,elf):
    if len(dol)<256 or len(elf)<HEADER.size:raise ValueError('image')
    h=HEADER.unpack_from(elf)
    off,unit,n=h[6],h[11],h[12]
    if (h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or h[3]!=1 or h[8]!=HEADER.size
            or off<HEADER.size or unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf)):
        raise ValueError('ELF header')
    sections=[SECTION.unpack_from(elf,off+i*unit) for i in range(n)]
    found=[set() for _ in OBJECTS]
    def u32(at):return struct.unpack_from('>I',dol,at)[0]
    def check_range(addr,size):
        end=addr+size
        def overlap(base,length):return length and base<end and addr<base+length
        if not 0x80004000<=addr<end<=0x81800000 or addr&3:raise ValueError('object range')
        if any(overlap(u32(0x48+4*i),u32(0x90+4*i)) for i in range(7)):
            raise ValueError('object text overlap')
        data=False
        for i in range(11):
            base,length,offset=u32(0x64+4*i),u32(0xac+4*i),u32(0x1c+4*i)
            if not overlap(base,length):continue
            if data or not base<=addr<end<=base+length or offset<256 or offset+length>len(dol):
                raise ValueError('object DOL span')
            data=True
        if not data and not u32(0xd8)<=addr<end<=u32(0xd8)+u32(0xdc):
            raise ValueError('object DOL span')
    for sec in sections:
        if sec[1]!=2:continue
        at,size,link,unit=sec[4],sec[5],sec[6],sec[9]
        if (unit!=SYMBOL.size or size%unit or size>16*1024*1024 or at+size>len(elf)
                or not 0<link<len(sections)):raise ValueError('symbol table')
        strings_sec=sections[link]
        sa,sn=strings_sec[4:6]
        if strings_sec[1]!=3 or sa+sn>len(elf) or sn>32*1024*1024:raise ValueError('strings')
        strings=elf[sa:sa+sn]
        for pos in range(at,at+size,unit):
            name,addr,length,info,_,ndx=SYMBOL.unpack_from(elf,pos)
            if name>=len(strings):continue
            for i,label in enumerate(OBJECTS):
                if not strings.startswith(label+b'\0',name):continue
                if (info&15)!=1 or not 0<ndx<len(sections):raise ValueError('object type')
                obj=sections[ndx]
                if (obj[1] not in (1,8) or obj[2]&7!=3 or not obj[3]<=addr<addr+length<=obj[3]+obj[5]
                        or (i<2 and length!=4) or (i>=2 and not 8<=length<=256) or length&3):
                    raise ValueError('object shape')
                if obj[1]==1 and (obj[4]+obj[5]>len(elf) or obj[4]<HEADER.size):
                    raise ValueError('object ELF span')
                check_range(addr,length)
                found[i].add((addr,length))
    for i,entries in enumerate(found):
        if len(entries)!=1:raise ValueError('object identity '+str(i))
    ranges=tuple(next(iter(x)) for x in found)
    if ranges[2][1]!=ranges[3][1]:raise ValueError('array shape')
    ordered=sorted(ranges)
    if any(a+n>b for (a,n),(b,_) in zip(ordered,ordered[1:])):raise ValueError('object overlap')
    return ranges

def inspect_leaf(root,words):
    """Bound the entire reachable control-flow graph, with both branch outcomes."""
    end=root+4*len(words)
    if not 1<=len(words)<=256 or root&3:raise ValueError('helper extent')
    work=[root];seen=set();stores=[];returns=0;backedges=0
    while work:
        pc=work.pop()
        if pc in seen:continue
        if not root<=pc<end or pc&3:raise ValueError('helper edge')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==19 and xo==16:
            if w&1 or ((w>>21)&20)!=20:raise ValueError('helper control')
            returns+=1
            continue
        if op==17 or (op==19 and xo in (50,528)):raise ValueError('helper control')
        if op==31 and xo in (146,467,150,1014):raise ValueError('helper control')
        if op in (16,18):
            if w&3:raise ValueError('helper edge')
            mask,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            target=pc+(((w&mask)^sign)-sign)
            if not root<=target<end:raise ValueError('helper edge')
            if target<=pc:backedges+=1
            work.append(target)
            if op==18:continue
        if op==36 or (op==31 and xo==151):
            stores.append((pc,op==31))
        elif op in (37,38,39,44,45,47,52,53,54,55,60,61) or (op==31 and xo in (183,215,247,407,439,661,662,725,918,663,695,727,759,983)):
            raise ValueError('helper store form')
        work.append(pc+4)
    if not returns or len(stores)!=4:raise ValueError('helper store count')
    return len(seen),sum(indexed for _,indexed in stores),returns,backedges

def derive(dol,elf):
    if hashlib.sha256(dol).hexdigest()!=OWNER_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('identity')
    if direct_bl(exact_words(dol,elf,CALL,1)[0],CALL)!=HELPER:raise ValueError('call identity')
    size=parse_functions(elf).get(HELPER,0)
    if not 4<=size<=1024 or size&3:raise ValueError('helper extent')
    ranges=layout(dol,elf)
    words=exact_words(dol,elf,HELPER,size//4)
    labels,indexed,returns,backedges=inspect_leaf(HELPER,words)
    return ranges[2][1]//4,labels,indexed,returns,backedges

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    allowed={'size','identity','image','ELF header','symbol table','strings','object type','object shape',
             'object ELF span','object range','object text overlap','object DOL span','object overlap','array shape',
             'call identity','helper extent','helper edge','helper control','helper store form','helper store count',
             'word identity','linked branch'}|{'object identity '+str(i) for i in range(4)}
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not HEADER.size<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        slots,labels,indexed,returns,backedges=derive(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        print('IPC_PROFILE_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
    print(f'IPC_PROFILE_GEOMETRY verified=1 objects=4 slots={slots} labels={labels} stores=4 indexed={indexed} returns={returns} backedges={backedges}')
    return 0
if __name__=='__main__':raise SystemExit(main())
