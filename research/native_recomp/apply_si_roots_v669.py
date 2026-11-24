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
def spans(dol,elf):
    geometry(dol,elf)
    sizes=parse_functions(elf);out=[]
    for pc in ROOTS:
        n=sizes.get(pc,0)
        if not 4<=n<=4096 or n&3:raise ValueError('SI root extent')
        exact(dol,elf,pc,n//4)
        out.append((pc,n))
    return tuple(out)
def pairs(ranges=TEST_SPANS):
    if tuple(pc for pc,_ in ranges)!=ROOTS or any(n&3 or not 4<=n<=4096 for pc,n in ranges):
        raise ValueError('SI roots')
    if any(a+n>b for (a,n),(b,_) in zip(ranges,ranges[1:])):raise ValueError('SI root overlap')
    root=ROOT+'''
    // Private ELF-authenticated SI interrupt route ownership.
    const auto si_owner=[](uint32_t a)->uint32_t {
'''+''.join(f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in ranges)+'''      return 0;
    };
    if(si_owner(func_start)&&si_owner(func_start)!=func_start)continue;'''
    read='''        const auto si_root=si_owner(current_pc);
        if((si_root&&si_root!=func_start)||(si_owner(func_start)&&si_root!=func_start))break;
'''+READ
    scanner=SCANNER+'\n    if('+'||'.join(f'func.start_address==0x{pc:08x}u' for pc,_ in ranges)+')func.hle_hook_name.clear();'
    return ((ROOT,root),(READ,read),(SCANNER,scanner))
def apply(root,ranges):
    p=root/'nWiiAnalyzer/src/analyzer.cpp'
    if p.is_symlink():raise ValueError('symlink')
    old=p.read_text(encoding='utf-8');new=rewrite(old,pairs(ranges))
    if new!=old:p.write_text(new,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        apply(a.root,spans(a.dol.read_bytes(),a.elf.read_bytes()))
    except (OSError,ValueError,UnicodeError):print('V669_SI_ANALYZER installed=0');return 1
    print('V669_SI_ANALYZER installed=1 roots=7 exact_dol_elf=1 scoped=1');return 0
if __name__=='__main__':raise SystemExit(main())
