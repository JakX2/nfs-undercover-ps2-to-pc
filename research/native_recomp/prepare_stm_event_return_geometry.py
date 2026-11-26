#!/usr/bin/env python3
"""Private STM post-IOCTL corridor to the outer interrupt restore call."""
import argparse
import struct
from pathlib import Path
from prepare_v629_stm_open import geometry,STM,EDGES
from prepare_v1337_open_completion import corridor,RESTORE
from prepare_v419_full_start import MAX_DOL,EXPECTED_GPRS
from make_private_elf_symbol_map import HEADER,SECTION,SYMBOL
from prepare_ipc_dispatch_geometry import credit_object
from prepare_ipc_profile_geometry import layout
from prepare_v1414_ipc_ring import ring_object
from prepare_v1383_stm_ioctl_entry import CALL

def object_at(dol,elf,addr,width):
    if len(dol)<256 or len(elf)<HEADER.size or width not in (1,2,4) or addr%width:
        raise ValueError('STM data request')
    h=HEADER.unpack_from(elf);off,unit,n=h[6],h[11],h[12]
    if h[0][:7]!=b'\x7fELF\x01\x02\x01' or h[2]!=20 or h[3]!=1 or h[8]!=HEADER.size or off<HEADER.size or unit!=SECTION.size or not 1<=n<10000 or off+n*unit>len(elf):
        raise ValueError('STM ELF sections')
    rows=[SECTION.unpack_from(elf,off+i*unit) for i in range(n)]
    found=set()
    for sec in rows:
        if sec[1]!=2:continue
        at,size,link,unit=sec[4],sec[5],sec[6],sec[9]
        if unit!=SYMBOL.size or size%unit or size>16*1024*1024 or at+size>len(elf) or not 0<link<len(rows):
            raise ValueError('STM symbol table')
        if rows[link][1]!=3 or rows[link][4]+rows[link][5]>len(elf):raise ValueError('STM strings')
        for pos in range(at,at+size,unit):
            _,a,length,info,_,ndx=SYMBOL.unpack_from(elf,pos)
            if info&15!=1 or not length or not a<=addr<addr+width<=a+length:continue
            if not 0<ndx<len(rows):raise ValueError('STM object section')
            obj=rows[ndx]
            if obj[1] not in (1,8) or obj[2]&7!=3 or not obj[3]<=a<a+length<=obj[3]+obj[5]:
                raise ValueError('STM object range')
            if obj[1]==1 and (obj[4]<HEADER.size or obj[4]+obj[5]>len(elf)):raise ValueError('STM object span')
            found.add((a,length))
    if len(found)!=1:raise ValueError('STM object identity')
    a,n=next(iter(found))
    if not 0x80004000<=a<a+n<=0x81800000 or n>4096:raise ValueError('STM object range')
    def u32(at):return struct.unpack_from('>I',dol,at)[0]
    def overlap(x,y):return y and x<a+n and a<x+y
    if any(overlap(u32(0x48+4*i),u32(0x90+4*i)) for i in range(7)):raise ValueError('STM text overlap')
    data=False
    for i in range(11):
        x,y,at=u32(0x64+4*i),u32(0xac+4*i),u32(0x1c+4*i)
        if not overlap(x,y):continue
        if data or not x<=a<a+n<=x+y or at<256 or at+y>len(dol):raise ValueError('STM DOL span')
        data=True
    if not data and not u32(0xd8)<=a<a+n<=u32(0xd8)+u32(0xdc):raise ValueError('STM DOL span')
    return a,n

def stores(root,body,labels,bases):
    out=[]
    for pc in labels:
        w=body[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op in (36,38,44):
            ra=(w>>16)&31;rs=(w>>21)&31
            if ra not in bases:raise ValueError('STM store base')
            imm=w&0xffff
            a=(bases[ra]+imm-(0x10000 if imm&0x8000 else 0))&0xffffffff
            n={36:4,38:1,44:2}[op]
            if a%n:raise ValueError('STM store alignment')
            out.append((pc,a,n,rs))
        elif op in (37,39,45,47,52,53,54,55,60,61) or (op==31 and xo in (150,151,183,215,247,407,439,661,662,725,918,663,695,727,759,983,1014)):
            raise ValueError('STM store form')
    if len(out)>8 or len({(a,n) for _,a,n,_ in out})!=len(out):raise ValueError('STM store count')
    return tuple(out)

def plan(d,e):
    _,body,_,_,_,_=geometry(d,e)
    start=CALL+4
    call,target=EDGES[-1]
    if target!=RESTORE:raise ValueError('STM restore edge')
    labels,exits=corridor(STM,body,start,call,target)
    if any(pc<start for pc in labels):raise ValueError('STM predecessor')
    rows=stores(STM,body,labels,{i:EXPECTED_GPRS[i] for i in (2,13)})
    objects=[object_at(d,e,a,n) for _,a,n,_ in rows]
    protected=[ring_object(d,e)[:2],credit_object(d,e),*layout(d,e)]
    for a,n in objects:
        if any(a<b+m and b<a+n for b,m in protected):raise ValueError('STM IPC object overlap')
    return labels,exits,rows,objects

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    allowed={'size','STM data request','STM ELF sections','STM symbol table','STM strings','STM object section','STM object range',
             'STM object span','STM object identity','STM text overlap','STM DOL span','STM store base','STM store alignment',
             'STM store form','STM store count','STM restore edge','STM predecessor','STM IPC object overlap'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not HEADER.size<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        labels,exits,rows,objects=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('STM_EVENT_RETURN_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'private_input'))
        return 1
    print(f'STM_EVENT_RETURN_GEOMETRY verified=1 labels={len(labels)} exits={len(exits)} stores={len(rows)} objects={len(set(objects))} word_stores={sum(x[2]==4 for x in rows)}')
    return 0
if __name__=='__main__':raise SystemExit(main())
