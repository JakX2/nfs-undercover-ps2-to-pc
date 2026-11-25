#!/usr/bin/env python3
"""Extend V816's original changed-ID lane through the original EXILock."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL
from prepare_v667_si_dispatch import exact,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
from prepare_owner_wireless_v816 import plan as old_plan,header as old_header,install as old_install
from prepare_owner_cancel_v754 import patch_analyzer
from prepare_owner_pair_v753 import alias,pair_shape
from audit_callback_frontiers_v799 import call_sites
from make_start_to_exi_transaction_v56 import LOCK,IRQMASK,SELECT,GETIRQ,UNMASK
from make_start_to_eximask_v53 import MASK
SETMASK=0x805266e0

def plan(dol,elf):
    roots,A,B,U,L,guards=old_plan(dol,elf)
    sizes=parse_functions(elf)
    if L!=LOCK or sizes.get(L)!=252:raise ValueError('lock extent')
    words=exact(dol,elf,L,63)
    sites=call_sites(L,words)
    if len(sites)!=7 or any(k!=1 for _,k,_ in sites) or [a for _,_,a in sites[1:-1]]!=[DISABLE,RESTORE,RESTORE,IRQMASK,RESTORE]:
        raise ValueError('lock edges')
    S,F=sites[0][2],sites[-1][2]
    first=exact(dol,elf,S,1)[0]
    count=32-((first>>21)&31)
    if not 1<=count<=18:raise ValueError('alias count')
    save=alias(dol,elf,S,sizes,count);restore=alias(dol,elf,F,sizes,count)
    sb,rb,disp=pair_shape(save,restore,count)
    wanted={IRQMASK:60,MASK:32,UNMASK:32,GETIRQ:4,SETMASK:151}
    for a,n in wanted.items():
        if a in roots or sizes.get(a)!=4*n:raise ValueError('mask extent')
        roots[a]=exact(dol,elf,a,n)
    if set(a for _,k,a in call_sites(IRQMASK,roots[IRQMASK]))!={MASK,UNMASK,GETIRQ}:raise ValueError('mask helper graph')
    for a in (MASK,UNMASK):
        if [v for _,k,v in call_sites(a,roots[a])]!=[DISABLE,SETMASK,RESTORE]:raise ValueError('mask leaf graph')
    for a in (GETIRQ,SETMASK):
        if call_sites(a,roots[a]):raise ValueError('mask leaf graph')
    if S in roots or F in roots or S==F:raise ValueError('alias overlap')
    roots.update({L:words,S:save,F:restore})
    guards=tuple(a for a in guards if a!=L)
    if SELECT not in guards:raise ValueError('select guard')
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>x for (_,y),(x,_) in zip(spans,spans[1:])):raise ValueError('root overlap')
    return (roots,A,B,U,L,guards),S,F,count,rb,disp

def header(p,out):
    q,S,F,n,rb,disp=p
    old_header(q,out)
    with out.open('a') as f:
        f.write('inline constexpr uint32_t '+','.join(f'{k}=0x{v:08x}u' for k,v in (
            ('SaveAlias',S),('RestoreAlias',F),('MaskHelper',IRQMASK),('Mask',MASK),('Unmask',UNMASK),
            ('SetMask',SETMASK),('GetIrq',GETIRQ),('SelectGuard',SELECT)))+';\n')
        f.write(f'inline constexpr unsigned AliasCount={n},RestoreBase={rb};\ninline constexpr int32_t AliasDisp={disp};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:
            old_install(q[0],a.output);print('V819_LOCK_NATIVE_ROUTE verified=1 mask_roots=5 exi_select_guard=1')
        elif a.patch_analyzer:patch_analyzer(q[0],a.output)
        else:
            header(q,a.output);print(f'V819_LOCK_GEOMETRY verified=1 lock_words=63 aliases={q[3]} mask_roots=5')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('lock extent','lock edges','alias count','mask extent','mask helper graph','mask leaf graph','alias overlap','select guard','root overlap','alias root','alias symbol','pair shape','frame offset','native coverage','native owner','native edge','hook identity','hook include','hook coverage')
        print('V819_LOCK_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
