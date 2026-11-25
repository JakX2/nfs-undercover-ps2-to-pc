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
from make_start_to_exi_transaction_v56 import LOCK,IRQMASK,SELECT,GETIRQ,UNMASK,PROBE,IMM
from make_start_to_eximask_v53 import MASK
from prepare_owner_wireless_lock_v819 import plan as lock_plan,header as lock_header
SETMASK=0x805266e0

def plan(dol,elf):
    q,S,F,n,rb,disp=lock_plan(dol,elf)
    roots,A,B,U,L,guards=q
    sizes=parse_functions(elf)
    if sizes.get(SELECT)!=304 or SELECT not in guards or IMM not in guards:
        raise ValueError('select extent')
    ws=exact(dol,elf,SELECT,76);sites=call_sites(SELECT,ws)
    if len(sites)!=8 or any(k!=1 for _,k,_ in sites):
        raise ValueError('select edges')
    s,f=sites[0][2],sites[-1][2]
    # V812 authenticated identical targets at ordinals 5 and 6.
    # Both are alternative calls to the same mask wrapper.
    ds=[a for _,_,a in sites[1:-1]]
    if ds[:3]!=[DISABLE,PROBE,RESTORE] or ds[3]!=ds[4] or ds[3] not in (MASK,UNMASK) or ds[-1]!=RESTORE:
        raise ValueError('select edges')
    k=32-((exact(dol,elf,s,1)[0]>>21)&31)
    if not 1<=k<=18:raise ValueError('alias count')
    save=alias(dol,elf,s,sizes,k);restore=alias(dol,elf,f,sizes,k)
    _,base,delta=pair_shape(save,restore,k)
    if (s==S)!=(f==F):raise ValueError('alias identity')
    if s==S:
        if list(roots[S])!=save or list(roots[F])!=restore:raise ValueError('alias identity')
    else:
        roots[s]=save;roots[f]=restore
    if PROBE in roots or sizes.get(PROBE)!=384:raise ValueError('probe extent')
    exact(dol,elf,PROBE,1);roots[PROBE]=[0x4e800020]
    roots[SELECT]=ws
    guards=tuple(a for a in guards if a!=SELECT)+(PROBE,)
    spans=sorted((a,a+4*len(ws)) for a,ws in roots.items())
    if any(y>x for (_,y),(x,_) in zip(spans,spans[1:])):raise ValueError('alias overlap')
    return ((roots,A,B,U,L,guards),S,F,n,rb,disp),s,f,k,base,delta

def header(p,out):
    q,s,f,n,base,delta=p
    lock_header(q,out)
    with out.open('a') as fobj:
        fobj.write(f'inline constexpr uint32_t SelectSave=0x{s:08x}u,SelectRestore=0x{f:08x}u,ImmGuard=0x{IMM:08x}u;\n')
        fobj.write(f'inline constexpr unsigned SelectCount={n},SelectBase={base};\ninline constexpr int32_t SelectDisp={delta};\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('output',type=Path)
    m=p.add_mutually_exclusive_group();m.add_argument('--install',action='store_true');m.add_argument('--patch-analyzer',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        q=plan(a.dol.read_bytes(),a.elf.read_bytes())
        if a.install:
            old_install(q[0][0],a.output);print('V825_SELECT_NATIVE_ROUTE verified=1 original_select=1 immediate_guard=1')
        elif a.patch_analyzer:patch_analyzer(q[0][0],a.output)
        else:
            header(q,a.output);print(f'V825_SELECT_GEOMETRY verified=1 select_words=76 aliases={q[3]} shared={int(q[1]==q[0][1])}')
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('select extent','select edges','alias identity','probe extent','lock extent','lock edges','alias count','mask extent','mask helper graph','mask leaf graph','alias overlap','select guard','root overlap','alias root','alias symbol','pair shape','frame offset','native coverage','native owner','native edge','hook identity','hook include','hook coverage')
        print('V825_SELECT_PREP verified=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
