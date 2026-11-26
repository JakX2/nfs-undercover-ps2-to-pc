#!/usr/bin/env python3
"""Private census of the larger diagnostic formatting target."""
import argparse,struct
from pathlib import Path
from prepare_post_stm_sc_report_helper_fixture import plan as helper_plan
from prepare_post_stm_sc_report_helper import census
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category
from audit_handler_suffix_v728 import target

def closure(root,words,start=None):
    # This is deliberately a first-boundary census, not a proof of
    # a variadic formatter's behavior or a prediction of its output.
    end=root+4*len(words);work=[root if start is None else start];seen=set();boundaries=set();back=0
    while work:
        pc=work.pop()
        if pc in seen:continue
        if not root<=pc<end or pc&3:raise ValueError('formatter escape')
        if len(seen)>=256:raise ValueError('formatter region cap')
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        if (op==18 and w&1) or w==0x4e800020 or (op==19 and xo in (16,528,50)) or op==17:
            boundaries.add(pc);continue
        if op in (16,18):
            if w&3:raise ValueError('formatter branch')
            dst=target(pc,w)
            if dst<=pc:back+=1
            work.append(dst)
            if op==16 and (w>>21)&20!=20:work.append(pc+4)
        else:work.append(pc+4)
    if not boundaries:raise ValueError('formatter boundary')
    return seen,boundaries,back

def plan(d,e):
    prior=helper_plan(d,e);root=prior[3][0]
    ws=exact_words(d,e,root,30)
    edges,*_=census(root,ws)
    if len(edges)!=2:raise ValueError('formatter caller')
    second=edges[max(edges)]
    sizes=parse_functions(e)
    if sizes.get(second)!=535*4:raise ValueError('formatter extent')
    body=exact_words(d,e,second,535)
    seen,bounds,back=closure(second,body)
    kinds={}
    for pc in seen:
        k=category(body[(pc-second)//4]);kinds[k]=kinds.get(k,0)+1
    deps=[]
    for pc in sorted(bounds):
        w=body[(pc-second)//4]
        if w>>26==18 and w&3==1:
            dst=direct_bl(w,pc);n=sizes.get(dst,0)
            if not 4<=n<=65536 or n%4:raise ValueError('formatter target')
            exact_words(d,e,dst,1);deps.append(n//4)
    return len(body),len(seen),len(bounds),back,kinds,deps

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','formatter escape','formatter region cap','formatter branch','formatter boundary','formatter caller','formatter extent','formatter target'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        words,seen,bounds,back,kinds,deps=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('POST_STM_SC_REPORT_FORMATTER_GEOMETRY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'POST_STM_SC_REPORT_FORMATTER_GEOMETRY verified=1 words={words} initial_region={seen} boundaries={bounds} backward={back} direct_dependencies={len(deps)} original_execution=0')
    print('POST_STM_SC_REPORT_FORMATTER_CLASSES '+' '.join(f'{k}={v}' for k,v in sorted(kinds.items())))
    for i,n in enumerate(deps,1):print(f'POST_STM_SC_REPORT_FORMATTER_TARGET ordinal={i} words={n}')
    return 0
if __name__=='__main__':raise SystemExit(main())
