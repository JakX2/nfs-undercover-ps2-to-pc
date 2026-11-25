#!/usr/bin/env python3
"""Focused full original SITransfer early return, with exact IRQ and GPR restore."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_owner_transfer_choice_v878 import plan as choice_plan,header as choice_header,choice
from prepare_owner_callback_prefix_v797 import install
from prepare_owner_cancel_v754 import patch_analyzer
from audit_os_leaf_v703 import plan as leaf_plan
from prepare_owner_pair_v753 import alias,pair_shape
from prepare_owner_handler_tail_v879 import tail_geometry
from make_private_elf_symbol_map import parse_functions

def plan(dol,elf):
    q,rows,guards,edges,stops=choice_plan(dol,elf);base=q[0]
    roots,C,S,_,_,_=base
    qs,Q=edges[2];rs,R=edges[-1];code=roots[C]
    _,_,r=leaf_plan(dol,elf)
    if Q!=r[1] or tuple(o for _,_,o,_ in stops)!=(3,4):raise ValueError('early restore target')
    extra,ends=choice(C,code,qs+4)
    if len(ends)!=1 or ends[0][1:]!=(1,9,R):raise ValueError('early restore path')
    tail=code[(rs-C)//4+1:(rs-C)//4+5]
    tail_geometry(tail)
    restore=alias(dol,elf,R,parse_functions(elf),11)
    pair_shape(roots[S],restore,11)
    if Q not in guards or R not in guards or Q==R:raise ValueError('early restore ownership')
    roots[Q]=r[5];roots[R]=restore
    guards=[x for x in guards if x not in (Q,R)]
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('early restore ownership')
    return (q,rows,guards,edges,stops),extra,Q,qs,R,rs,tail

def header(p,out):
    q,extra,Q,qs,R,rs,tail=p;roots,C,*_=q[0][0]
    choice_header(q,out)
    f=lambda w:f'0x{w:08x}u'
    with out.open('a') as h:
        h.write('inline constexpr uint32_t '+','.join(f'{k}={f(v)}' for k,v in (('Q',Q),('IrqCall',qs),('IrqResume',qs+4),('R',R),('RestoreCall',rs)))+';\n')
        for name,words in (('irq_restore_words',roots[Q]),('restore_words',roots[R]),('tail_words',tail)):
            h.write(f'inline constexpr std::array<uint32_t,{len(words)}> {name}{{'+','.join(map(f,words))+'};\n')
        h.write(f'inline constexpr std::array<undercover::wii::HandlerSuffixLabel,{len(extra)}> early_rows{{{{')
        h.write(','.join(f'{{{f(pc)},{f(w)},{o}u,{k}u}}' for pc,(w,o,k) in sorted(extra.items())))
        h.write('}};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());base=q[0][0][0];C=base[1]
        if a.install:install(base,a.output,extra_links=tuple((C,pc,dst) for pc,dst in q[0][3][1:]),use_reachable=True)
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            header(q,a.output);print(f'V880_TRANSFER_EARLY_GEOMETRY verified=1 suffix={len(q[1])} restore_gprs=11 irq_words=9 tail_words=4 execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('early restore target','early restore path','early restore ownership','handler tail extent','handler tail shape','handler tail frame','transfer choice census','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V880_TRANSFER_EARLY_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
