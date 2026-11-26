#!/usr/bin/env python3
"""Aggregate control-flow census of the next authenticated formatter dependency.

All original words and addresses are kept in process memory; no extracts or
private metadata are emitted. This is static analysis, not native execution.
"""
import argparse
import struct
from collections import Counter
from pathlib import Path
from prepare_post_stm_sc_report_formatter_path import plan as prefix_plan
from prepare_post_stm_sc_formatter_leaf_path import run as leaf_run
from prepare_post_stm_sc_formatter_resume_path import resume
from prepare_v419_full_start import MAX_DOL,direct_bl
from make_private_elf_symbol_map import parse_functions
from make_v624_ipc_geometry import exact_words
from audit_osinit_suffix_v929 import category

def signed(v,bits):
    return (v^(1<<(bits-1)))-(1<<(bits-1))

def relative_target(pc,w):
    if w&2:raise ValueError('absolute branch')
    return pc+signed(w&(0xfffc if w>>26==16 else 0x03fffffc),16 if w>>26==16 else 26)

def census(root,words,*,stop_at_calls):
    if not words or len(words)>16384 or root&3:raise ValueError('function geometry')
    end=root+4*len(words);seen=set();todo=[root];edges=set();bounds={};calls={};back=set()
    def edge(pc,dst):
        if not root<=dst<end or dst&3:raise ValueError('local edge escape')
        edges.add((pc,dst));todo.append(dst)
        if dst<=pc:back.add((pc,dst))
    while todo:
        pc=todo.pop()
        if pc in seen:continue
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023;bo=(w>>21)&31
        if op in (16,18):
            dst=relative_target(pc,w)
            conditional=op==16 and (bo&20)!=20
            if w&1:
                if root<=dst<end:
                    # Do not silently collapse a linked local branch into an
                    # ordinary call/return edge; its LR contract is unknown.
                    raise ValueError('linked local branch')
                calls[pc]=dst;bounds[pc]='direct_call'
                if not stop_at_calls or conditional:edge(pc,pc+4)
            elif root<=dst<end:
                edge(pc,dst)
                if conditional:edge(pc,pc+4)
            else:
                bounds[pc]='direct_tail'
                if conditional:edge(pc,pc+4)
        elif op==19 and xo in (16,528):
            conditional=(bo&20)!=20
            if xo==528 and not bo&4:raise ValueError('invalid ctr branch')
            kind=('indirect_call' if w&1 else 'return' if xo==16 else 'indirect_tail')
            bounds[pc]=kind
            if conditional or (w&1 and not stop_at_calls):edge(pc,pc+4)
        elif op==17 or (op==19 and xo==50):
            bounds[pc]='system'
        else:edge(pc,pc+4)
    if not bounds:raise ValueError('no boundaries')
    kinds=Counter(category(words[(pc-root)//4]) for pc in seen)
    boundary_kinds=Counter(bounds.values())
    return {'visited':len(seen),'edges':len(edges),'backedges':len(back),
            'categories':kinds,'boundaries':boundary_kinds,'calls':calls}

def plan(d,e):
    path,frame,accesses,saved,leaf_root,gp,mem,ws,state,readonly=prefix_plan(d,e,details=True)
    leaf=leaf_run(leaf_root,exact_words(d,e,leaf_root,12),gp,readonly,mem,initial_cr=state[2],details=True)
    if len(leaf[0])!=8 or len(leaf[1])!=1 or len(leaf[3])!=12:raise ValueError('leaf predecessor')
    result=resume(path[0],ws,(path,frame,accesses,saved,leaf_root,gp,mem,state),leaf,readonly)
    active,_,sites,_,root,out_gp,*_=result
    if len(active)!=10 or sites or direct_bl(ws[(active[-1]-path[0])//4],active[-1])!=root:
        raise ValueError('continuation predecessor')
    sizes=parse_functions(e)
    if sizes.get(root)!=383*4:raise ValueError('dependency geometry')
    words=exact_words(d,e,root,383)
    first=census(root,words,stop_at_calls=True)
    full=census(root,words,stop_at_calls=False)
    call_sizes=[]
    for dst in sorted(set(full['calls'].values())):
        n=sizes.get(dst,0)
        if not 4<=n<=65536 or n%4:raise ValueError('call target geometry')
        exact_words(d,e,dst,1)
        call_sizes.append(n//4)
    w=words[0]
    entry_frame=-(signed(w&0xffff,16)) if w>>26==37 and (w>>21)&31==1 and (w>>16)&31==1 else 0
    if entry_frame<0 or entry_frame%8:raise ValueError('entry frame geometry')
    args=Counter(k for k,_ in out_gp[3:11])
    return first,full,call_sizes,entry_frame,args

def main():
    a=argparse.ArgumentParser();a.add_argument('dol',type=Path);a.add_argument('elf',type=Path);q=a.parse_args()
    safe={'size','function geometry','local edge escape','absolute branch','linked local branch','invalid ctr branch',
          'no boundaries','leaf predecessor','continuation predecessor','dependency geometry','call target geometry','entry frame geometry'}
    try:
        if not 256<=q.dol.stat().st_size<=MAX_DOL or not 52<=q.elf.stat().st_size<=64*1024*1024:raise ValueError('size')
        first,full,targets,frame,args=plan(q.dol.read_bytes(),q.elf.read_bytes())
    except (OSError,ValueError,KeyError,IndexError,TypeError,struct.error) as ex:
        print('FORMATTER_NEXT_DEPENDENCY verified=0 reason='+(str(ex).replace(' ','_') if str(ex) in safe else 'private_input'))
        return 1
    print(f'FORMATTER_NEXT_DEPENDENCY verified=1 words=383 first_region={first["visited"]} full_region={full["visited"]} entry_frame={frame} distinct_calls={len(targets)} original_execution=0')
    for name,obj in (('FIRST',first),('FULL',full)):
        print(f'FORMATTER_NEXT_{name} edges={obj["edges"]} backedges={obj["backedges"]} '+' '.join(f'{k}={v}' for k,v in sorted(obj['boundaries'].items())))
        print(f'FORMATTER_NEXT_{name}_CLASSES '+' '.join(f'{k}={v}' for k,v in sorted(obj['categories'].items())))
    print('FORMATTER_NEXT_ARGUMENT_KINDS '+' '.join(f'{k}={v}' for k,v in sorted(args.items())))
    for i,n in enumerate(sorted(targets),1):print(f'FORMATTER_NEXT_TARGET ordinal={i} words={n}')
    return 0
if __name__=='__main__':raise SystemExit(main())
