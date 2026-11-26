#!/usr/bin/env python3
"""Authenticate original synchronous IOS_Open completion without execution."""
import argparse,struct
from pathlib import Path
from make_v651_open_fixture import submit_geometry,SUBMIT,OPEN
from make_v639_open_geometry import geometry as open_geometry
from make_v1243_stm_fixture import seed_data
from prepare_v629_stm_open import geometry as stm_geometry,STM,FIRST_OPEN_CALL
from make_v1252_sleep_fixture import geometry as sleep_geometry,SLEEP
from apply_open_roots_v645 import irq_spans
from make_v624_ipc_geometry import exact_words
from prepare_v419_full_start import MAX_DOL,direct_bl,words_at
from prepare_v1281_reply_fixture import symbols
from prepare_v1321_combined_resume import scope as combined_scope
from prepare_v1260_scheduler_vector import SOURCE,SC_SOURCE,VECTORS,BLR
from prepare_v453_debug_leaf import data_at
from make_v626_ipc_fixture import assemble
SECOND=0x8052b0b4
FREE=0x8051ad3c
DISABLE=0x805265ac
RESTORE=0x805265d4

def corridor(root,words,start,stop,target):
    if not root<=start<=stop<root+4*len(words) or (root|start|stop|target)&3:
        raise ValueError('completion corridor')
    if direct_bl(words[(stop-root)//4],stop)!=target:raise ValueError('completion call')
    seen=set();exits=set();work=[start];reached=False
    while work:
        pc=work.pop()
        if pc in seen:continue
        if not root<=pc<=stop:
            exits.add(pc);continue
        seen.add(pc)
        if pc==stop:reached=True;continue
        w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if op in (16,18):
            if w&3:raise ValueError('completion control')
            m,s=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
            dst=(pc+((w&m)^s)-s)&0xffffffff
            work.append(dst)
            if op==16 and (w>>21)&20!=20:work.append(pc+4)
        elif op==17 or (op==19 and xo in (16,50,528)) or (op==31 and xo==146):
            raise ValueError('completion control')
        else:work.append(pc+4)
    if not reached:raise ValueError('completion unreachable')
    return tuple(sorted(seen)),tuple(sorted(exits))

def plan(dol,elf):
    bridge,body,_,_,paths,_=stm_geometry(dol,elf)
    sub,edges=submit_geometry(dol,elf)
    _,_,op=open_geometry(dol,elf)
    sleep,sleep_edges,_=sleep_geometry(dol,elf)
    shared={SLEEP:tuple(sleep),SUBMIT:tuple(sub[SUBMIT]),FREE:tuple(sub[FREE]),OPEN:tuple(op[OPEN])}
    shared.update({a:tuple(exact_words(dol,elf,a,n//4)) for a,n in irq_spans(dol,elf)})
    sites=((SLEEP,0x8052a500,RESTORE),(SUBMIT,0x805197dc,RESTORE),(SUBMIT,0x80519804,FREE),
           (FREE,0x8051ad60,DISABLE),(FREE,0x8051af04,RESTORE),(OPEN,0x80519a38,SUBMIT))
    rows=[]
    for owner,pc,dst in sites:
        ws=shared[owner];i=(pc-owner)//4
        if not 0<=i<len(ws) or direct_bl(ws[i],pc)!=dst:raise ValueError('completion edge')
        rows.append((dst,pc+4,ws[i],shared[dst][0]))
    old=tuple(body[:(FIRST_OPEN_CALL-STM)//4+1])
    new=tuple(body[:(SECOND-STM)//4+1])
    if len(old)!=23 or len(new)!=33 or direct_bl(old[-1],FIRST_OPEN_CALL)!=OPEN:raise ValueError('completion prefix')
    visits,exits=corridor(STM,new,FIRST_OPEN_CALL+4,SECOND,OPEN)
    old_data=seed_data(dol,old,paths);data=seed_data(dol,new,paths)
    if any(data.get(a)!=v for a,v in old_data.items()):raise ValueError('completion data')
    return shared,tuple(rows),old,new,visits,exits,data,old_data

def merge(blocks,shared,old,new):
    if len(old)!=23 or len(new)!=33 or tuple(new[:len(old)])!=old or blocks.get(STM)!=old+(BLR,):
        raise ValueError('completion predecessor')
    if any(blocks.get(a)!=ws for a,ws in shared.items()):raise ValueError('completion shared identity')
    out={**blocks,STM:new+(BLR,)}
    spans=sorted((pc,pc+4*len(ws)) for pc,ws in out.items())
    if len(out)+2>48 or any(end>b for (_,end),(b,_) in zip(spans,spans[1:])):raise ValueError('completion ownership')
    return out

def verify(dol,elf,raw,csv):
    shared,edges,old,new,visits,exits,data,old_data=plan(dol,elf)
    sizes=symbols(csv)
    blocks={a:words_at(raw,a,n//4) for a,n in sizes.items()}
    expanded=merge(blocks,shared,old,new)
    prior=dict(combined_scope(dol,elf,sizes))
    if STM in prior and prior[STM]!=4*(len(old)+1):raise ValueError('completion ownership')
    prior[STM]=4*(len(new)+1)
    spans=sorted(prior.items())
    if any(a+n>b for (a,n),(b,_) in zip(spans,spans[1:])):raise ValueError('completion ownership')
    table=data_at(raw,VECTORS,60)
    out=bytearray(assemble({**expanded,SOURCE:words_at(raw,SOURCE,38),SC_SOURCE:words_at(raw,SC_SOURCE,7)},ROOT,max_roots=48))
    for off,v in ((0x1c,len(out)),(0x64,VECTORS),(0xac,len(table))):struct.pack_into('>I',out,off,v)
    image=bytes(out)+table
    if any(words_at(image,a,len(ws))!=ws for a,ws in expanded.items()):raise ValueError('completion roundtrip')
    print(f'V1337_COMPLETION_PREFLIGHT verified=1 roots={len(expanded)+2} shared_roots={len(shared)} direct_edges={len(edges)+2} stm_original_words={len(new)} continuation_labels={len(visits)} alternate_exits={len(exits)} additional_seed_bytes={len(data)-len(old_data)} original_execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    try:
        if not 256<=a.dol.stat().st_size<=MAX_DOL or not 52<=a.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        verify(a.dol.read_bytes(),a.elf.read_bytes(),(a.out/'fixture.dol').read_bytes(),(a.out/'symbols.csv').read_text());return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        allowed=('size','completion corridor','completion call','completion control','completion unreachable','completion edge','completion prefix','completion data','completion predecessor','completion shared identity','completion ownership','completion roundtrip')
        print('V1337_COMPLETION_PREFLIGHT verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in allowed else 'prior_or_io'));return 1
if __name__=='__main__':raise SystemExit(main())
