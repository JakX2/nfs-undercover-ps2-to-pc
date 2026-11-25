#!/usr/bin/env python3
"""Bounded original-free CFG census; owner mode emits only classifications."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v668_si_ack import is_word_store
from prepare_v672_si_ack_route import call_census
from prepare_v667_si_dispatch import exact,TIME,DISABLE,RESTORE,SCHED
from make_private_elf_symbol_map import parse_functions
from si_second_geometry_v688 import second_plan
from classify_save_leaf_v683 import inspect_suffix,symbol_evidence
def target(pc,w):
    op=w>>26
    if op not in (16,18):raise ValueError('branch')
    bits,sign=(0xfffc,0x8000) if op==16 else (0x03fffffc,0x02000000)
    d=((w&bits)^sign)-sign
    return (d if w&2 else pc+d)&0xffffffff
def prefix(root,words):
    """Overapproximate reachable labels until a call, return or exception."""
    if root&3 or not 1<=len(words)<=1024:raise ValueError('extent')
    end=root+4*len(words);calls=call_census(root,words)
    todo=[root];seen=set();first=set();stores=returns=edges_out=unknown=0
    while todo:
        pc=todo.pop()
        if pc in seen:continue
        if pc&3 or not root<=pc<end:
            edges_out+=1;continue
        seen.add(pc);w=words[(pc-root)//4];op=w>>26;xo=(w>>1)&1023
        stores+=is_word_store(w)
        if pc in calls:
            first.add(calls[pc][0]);continue
        if w==0x4e800020:returns+=1;continue
        if op==17 or op==19 and xo in (16,50,528) or op==31 and xo==146:
            unknown+=1;continue
        if op in (16,18):
            if w&1:
                unknown+=1;continue
            todo.append(target(pc,w))
            if op==16:todo.append(pc+4)
        else:todo.append(pc+4)
    return dict(labels=len(seen),stores=stores,returns=returns,outside=edges_out,unknown=unknown,
                first_calls=tuple(sorted(first)))
def classify(dol,elf):
    _,root,_,_,words=second_plan(dol,elf)
    result=prefix(root,words);sizes=parse_functions(elf)
    rows=[]
    for pc,(ordinal,kind) in sorted(call_census(root,words).items()):
        if kind!=1:raise ValueError('unexpected indirect')
        dst=target(pc,words[(pc-root)//4]);n=sizes.get(dst,0)
        row=dict(ordinal=ordinal,first_reachable=int(ordinal in result['first_calls']),
                 exact_root=int(bool(n)),containing=sum(a<dst<a+s for a,s in sizes.items()),
                 words=0,identity=0,returns=0,calls=0,stores=0,
                 known_time=int(dst==TIME),known_disable=int(dst==DISABLE),
                 known_restore=int(dst==RESTORE),known_sched=int(dst==SCHED),save_kind=0,save_registers=0)
        if n and not n&3 and n<=4096:
            code=exact(dol,elf,dst,n//4)
            row.update(words=len(code),identity=1,returns=code.count(0x4e800020),
                       stores=sum(is_word_store(w) for w in code),
                       calls=sum(bool(w&1) and (w>>26 in (16,18) or w>>26==19 and (w>>1)&1023 in (16,528)) for w in code))
        row.update(symbol_evidence(elf,dst))
        try:
            save=inspect_suffix(dol,elf,dst)
            row.update(save_kind=save['kind'],save_registers=save['registers'])
        except ValueError:pass
        rows.append(row)
    return result,rows
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        summary,rows=classify(a.dol.read_bytes(),a.elf.read_bytes())
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V690_SI_NESTED inspected=0');return 1
    print('V690_SI_PREFIX inspected=1 '+' '.join(f'{k}={len(v) if isinstance(v,tuple) else v}' for k,v in summary.items()))
    for row in rows:print('V690_SI_NESTED inspected=1 '+' '.join(f'{k}={v}' for k,v in row.items()))
    return 0
if __name__=='__main__':raise SystemExit(main())
