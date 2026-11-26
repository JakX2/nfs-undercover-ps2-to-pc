#!/usr/bin/env python3
"""Private profiling-return to mailbox-control geometry; no original data exported."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL,ORIGINAL_SHA256
from prepare_v419_full_start import MAX_DOL,OWNER_SHA,direct_bl
from make_v651_open_fixture import submit_geometry,SUBMIT
from make_start_to_ipc_submit_v72 import EDGES
from prepare_v1414_ipc_ring import ring_object

def credit_object(dol,elf):
    if len(dol)<256 or len(elf)<HEADER.size:raise ValueError('credit image')
    h=HEADER.unpack_from(elf);off,unit,n=h[6],h[11],h[12]
    if (h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or h[3]!=1 or h[8]!=HEADER.size
            or off<HEADER.size or unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf)):
        raise ValueError('credit ELF header')
    sections=[SECTION.unpack_from(elf,off+i*unit) for i in range(n)]
    found=set()
    for sec in sections:
        if sec[1]!=2:continue
        at,size,link,unit=sec[4],sec[5],sec[6],sec[9]
        if (unit!=SYMBOL.size or size%unit or size>16*1024*1024 or at+size>len(elf)
                or not 0<link<len(sections)):raise ValueError('credit symbols')
        st=sections[link];sa,sn=st[4:6]
        if st[1]!=3 or sa+sn>len(elf) or sn>32*1024*1024:raise ValueError('credit strings')
        strings=elf[sa:sa+sn]
        for pos in range(at,at+size,unit):
            name,addr,length,info,_,ndx=SYMBOL.unpack_from(elf,pos)
            if name>=len(strings) or not strings.startswith(b'__mailboxAck\0',name):continue
            if (info&15)!=1 or not 0<ndx<len(sections):raise ValueError('credit type')
            obj=sections[ndx]
            if (length!=4 or addr&3 or obj[1] not in (1,8) or obj[2]&7!=3 or
                not obj[3]<=addr<addr+4<=obj[3]+obj[5] or not 0x80004000<=addr<addr+4<=0x81800000):
                raise ValueError('credit shape')
            if obj[1]==1 and (obj[4]<HEADER.size or obj[4]+obj[5]>len(elf)):
                raise ValueError('credit ELF span')
            found.add((addr,length))
    if len(found)!=1:raise ValueError('credit identity')
    addr,length=next(iter(found))
    def u32(at):return struct.unpack_from('>I',dol,at)[0]
    def overlap(base,size):return size and base<addr+length and addr<base+size
    if any(overlap(u32(0x48+4*i),u32(0x90+4*i)) for i in range(7)):
        raise ValueError('credit text overlap')
    data=False
    for i in range(11):
        base,size,offset=u32(0x64+4*i),u32(0xac+4*i),u32(0x1c+4*i)
        if not overlap(base,size):continue
        if data or not base<=addr<addr+length<=base+size or offset<256 or offset+size>len(dol):
            raise ValueError('credit DOL span')
        data=True
    if not data and not u32(0xd8)<=addr<addr+length<=u32(0xd8)+u32(0xdc):
        raise ValueError('credit DOL span')
    return addr,length

def corridor(root,words,start,first,read,second,calls):
    end=root+4*len(words)
    if not root<=start<first<read<second<end or second-start>512 or any(x&3 for x in (start,first,read,second)):
        raise ValueError('dispatch extent')
    if not all(x in calls for x in (first,read,second)) or calls[first]!=calls[second] or calls[read]==calls[first]:
        raise ValueError('dispatch call roles')
    graph={};exits=set();work=[start]
    while work:
        pc=work.pop()
        if pc in graph:continue
        if not start<=pc<=second or pc&3:raise ValueError('dispatch internal edge')
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if pc in calls:
            if direct_bl(w,pc)!=calls[pc]:raise ValueError('dispatch call identity')
        elif op==18 and w&1:raise ValueError('dispatch unknown call')
        if pc==second:
            graph[pc]=();continue
        successors=[pc+4]
        if op in (16,18) and not(w&1):
            if w&2:raise ValueError('dispatch absolute branch')
            mask,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            target=pc+(((w&mask)^sign)-sign)
            if not root<=target<end:raise ValueError('dispatch external branch')
            successors=[target] if op==18 or ((w>>21)&20)==20 else [pc+4,target]
        elif op==16 and w&1 or op==17 or (op==19 and xo in (16,50,528)):
            raise ValueError('dispatch control')
        graph[pc]=tuple(x for x in set(successors) if start<=x<=second)
        exits.update((pc,x) for x in successors if not start<=x<=second)
        work.extend(graph[pc])
    def reaches(src,dst,blocked=None):
        todo=[src];seen=set()
        while todo:
            x=todo.pop()
            if x==blocked or x in seen:continue
            if x==dst:return True
            seen.add(x);todo.extend(graph.get(x,()))
        return False
    if not reaches(start,second) or not reaches(first,read) or not reaches(read,second):
        raise ValueError('dispatch route')
    if reaches(start,second,first) or reaches(start,second,read):
        raise ValueError('dispatch dominance')
    lane={pc for pc in graph if reaches(pc,second)}
    def store(pc):
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op==36:return 1
        if op==31 and xo==151:return 2
        if op in (37,38,39,44,45,47,52,53,54,55,60,61) or (op==31 and xo in
                (150,183,215,247,407,439,661,662,725,918,663,695,727,759,983,1014)):
            return 3
        return 0
    stores=[store(pc) for pc in lane if first<pc<second and store(pc)]
    if 3 in stores:raise ValueError('dispatch store form')
    if len(stores)!=3:raise ValueError('dispatch store count')
    return len(lane),len(exits),sum(bool(store(pc)) for pc in lane if pc<first),len(stores),stores.count(2)

def derive(d,e):
    if hashlib.sha256(d).hexdigest()!=OWNER_SHA or hashlib.sha256(e).hexdigest()!=ORIGINAL_SHA256:
        raise ValueError('identity')
    roots,_=submit_geometry(d,e)
    ring=ring_object(d,e);credit=credit_object(d,e)
    if ring[0]<credit[0]+credit[1] and credit[0]<ring[0]+ring[1]:
        raise ValueError('credit ring overlap')
    start=EDGES[3][0]+4
    first,read,second=(x[0] for x in EDGES[6:9])
    return corridor(SUBMIT,roots[SUBMIT],start,first,read,second,dict(EDGES))

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    allowed={'size','identity','credit image','credit ELF header','credit symbols','credit strings','credit type','credit shape',
             'credit ELF span','credit identity','credit text overlap','credit DOL span','credit ring overlap','dispatch extent',
             'dispatch call roles','dispatch internal edge','dispatch call identity','dispatch unknown call','dispatch absolute branch',
             'dispatch external branch','dispatch control','dispatch route','dispatch dominance','dispatch store form','dispatch store count','linked branch'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not HEADER.size<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        labels,exits,pre,stores,indexed=derive(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,struct.error) as ex:
        print('IPC_DISPATCH_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
    print(f'IPC_DISPATCH_GEOMETRY verified=1 credit=1 ring=1 labels={labels} exits={exits} pre_stores={pre} post_stores={stores} indexed={indexed}')
    return 0
if __name__=='__main__':raise SystemExit(main())
