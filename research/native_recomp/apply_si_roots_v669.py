#!/usr/bin/env python3
"""Restrict native SI-dispatch label ownership to authenticated ELF spans."""
import argparse
from pathlib import Path
from apply_irq_bootstrap_v475 import rewrite
from apply_bat_roots_v586 import ROOT,READ
from apply_stm_native_open_v632 import OLD as SCANNER
from prepare_v667_si_dispatch import geometry,exact,DISPATCH,HANDLER,SCHED,TIME,DISABLE,RESTORE
from make_private_elf_symbol_map import parse_functions
TRAMP=0x80526ce0
ROOTS=tuple(sorted({DISPATCH,HANDLER,SCHED,TIME,DISABLE,RESTORE,TRAMP}))
TEST_SPANS=tuple((r,4) for r in ROOTS)
def spans(dol,elf,first_helper=False):
    geometry(dol,elf)
    sizes=parse_functions(elf);out=[]
    for pc in ROOTS:
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3:raise ValueError('SI root extent')
        exact(dol,elf,pc,n//4)
        out.append((pc,n))
    if first_helper:
        from si_helper_geometry_v680 import helper_plan
        (_,target,size,_,_),alias,_=helper_plan(dol,elf)
        if not alias and target not in ROOTS:out.append((target,size))
    return tuple(sorted(out))
def pairs(ranges=TEST_SPANS,alias=0):
    if not set(ROOTS).issubset(pc for pc,_ in ranges) or len(ranges) not in (7,8) or tuple(sorted(set(pc for pc,_ in ranges)))!=tuple(pc for pc,_ in ranges) or any(n&3 or not 4<=n<=4096 for pc,n in ranges):
        raise ValueError('SI roots')
    if any(a+n>b for (a,n),(b,_) in zip(ranges,ranges[1:])):raise ValueError('SI root overlap')
    if alias and (alias&3 or not 0x80000000<=alias<0x81800000 or any(a<=alias<a+n for a,n in ranges)):raise ValueError('first SI alias overlap')
    root=ROOT+'''
    // Private ELF-authenticated SI interrupt route ownership.
    const auto si_owner=[](uint32_t a)->uint32_t {
'''+''.join(f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in ranges)+'''      return 0;
    };
    if(si_owner(func_start)&&si_owner(func_start)!=func_start)continue;'''
    read='''        const auto si_root=si_owner(current_pc);
        if((si_root&&si_root!=func_start)||(si_owner(func_start)&&si_root!=func_start))break;
'''+READ
    scanner=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc in (*[a for a,_ in ranges],*([alias] if alias else [])))+')func.hle_hook_name.clear();'
    return ((ROOT,root),(READ,read),(SCANNER,scanner))
def apply(root,ranges,alias=0):
    p=root/'nWiiAnalyzer/src/analyzer.cpp'
    if p.is_symlink():raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');new=rewrite(old,pairs(ranges,alias))
    if new!=old:p.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('--first-ack-helper',action='store_true');a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        dol,elf=a.dol.read_bytes(),a.elf.read_bytes()
        ranges=spans(dol,elf,a.first_ack_helper);alias=0
        if a.first_ack_helper:
            from si_helper_geometry_v680 import helper_plan
            (_,target,_,_,_),is_alias,_=helper_plan(dol,elf)
            if is_alias:alias=target
        apply(a.root,ranges,alias)
    except (OSError,ValueError,UnicodeError) as exc:
        reasons={'first SI dependency not direct':1,'first SI dependency extent':2,'first SI dependency return':3,'word identity':4,'SI root overlap':5,'SI roots':6,'SI root extent':7,'save leaf terminator':8,'save leaf shape':9,'save leaf extent':10,'save leaf sequence':11,'first SI alias containment':12,'first SI alias unsupported kind':13,'first SI alias overlap':14}
        print(f'V682_SI_ANALYZER_REFUSAL category={reasons.get(str(exc),0)}')
        print('V669_SI_ANALYZER installed=0');return 1
    print(f'V669_SI_ANALYZER installed=1 roots={len(ranges)} exact_dol_elf=1 scoped=1 shared_alias={int(bool(alias))}');return 0
if __name__=='__main__':raise SystemExit(main())
