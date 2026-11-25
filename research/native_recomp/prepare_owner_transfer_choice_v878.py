#!/usr/bin/env python3
"""Private original SITransfer choice after OSDisableInterrupts, before another call."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,direct_bl
from prepare_owner_transfer_disable_v874 import plan as disable_plan,write_header
from prepare_owner_callback_prefix_v797 import install
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_v667_si_dispatch import exact
from prepare_owner_pair_v753 import BLR,alias
from audit_handler_suffix_v728 import suffix,target
from make_private_elf_symbol_map import parse_functions
from audit_handler_third_v740 import names
from prepare_v868_handler_suffix import lane

def choice(root,words,start):
    n,b,s,stops=suffix(root,words,start)
    kinds=tuple((k,o) for _,k,o,_ in stops)
    if not 1<=n<=64 or b or s>8 or not kinds or any(k!=1 or not 3<=o<=9 for k,o in kinds):
        raise ValueError('transfer choice census')
    return lane(root,words,start,(n,b,s,kinds)),stops

def plan(dol,elf):
    q=disable_plan(dol,elf);base,D,ds,_,_=q
    roots,C,S,site,_,_=base;code=list(exact(dol,elf,C,91));sizes=parse_functions(elf)
    rows,stops=choice(C,code,ds+4)
    edges=[(C+4*i,direct_bl(w,C+4*i)) for i,w in enumerate(code) if w>>26==18 and w&3==1]
    if len(edges)!=9 or edges[:2]!=[(site,S),(ds,D)]:raise ValueError('transfer choice edges')
    expected=('OSRestoreInterrupts','__OSGetSystemTime','OSSetAlarm','__SITransfer','OSRestoreInterrupts','OSRestoreInterrupts')
    if tuple(names(elf,a) for _,a in edges[2:8])!=expected:raise ValueError('transfer choice names')
    alias(dol,elf,edges[8][1],sizes,11)
    guards=sorted({a for _,a in edges[2:]})
    for a in guards:
        if a in roots:raise ValueError('transfer choice overlap')
        exact(dol,elf,a,1);roots[a]=[BLR]
    roots[C]=code
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>u for (_,y),(u,_) in zip(spans,spans[1:])):raise ValueError('transfer choice overlap')
    return q,rows,guards,edges,stops

def header(p,out):
    q,rows,guards,_,_=p
    write_header(q,out)
    f=lambda w:f'0x{w:08x}u'
    with out.open('a') as h:
        h.write('#include "wii_handler_suffix_guard_v868.h"\n')
        h.write(f'inline constexpr std::array<uint32_t,{len(guards)}> guard_roots{{'+','.join(map(f,guards))+'};\n')
        h.write('inline constexpr std::array<uint32_t,1> guard_words{0x4e800020u};\n')
        h.write(f'inline constexpr std::array<undercover::wii::HandlerSuffixLabel,{len(rows)}> choice_rows{{{{')
        h.write(','.join(f'{{{f(pc)},{f(w)},{o}u,{k}u}}' for pc,(w,o,k) in sorted(rows.items())))
        h.write('}};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes());base=q[0][0];C=base[1]
        if a.install:install(base,a.output,extra_links=tuple((C,pc,dst) for pc,dst in q[3][1:]),use_reachable=True)
        elif a.patch_analyzer:patch_analyzer(base,a.output)
        else:
            header(q,a.output);print(f'V878_TRANSFER_CHOICE_GEOMETRY verified=1 labels={len(q[1])} boundaries={len(q[4])} ordinals='+','.join(str(o) for _,_,o,_ in q[4])+' execution=0')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('transfer choice census','transfer choice edges','transfer choice names','transfer choice overlap','handler suffix census','handler suffix extent','handler suffix control','handler suffix coverage','native coverage','native owner','hook identity','hook include','hook coverage','private output')
        print('V878_TRANSFER_CHOICE_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
