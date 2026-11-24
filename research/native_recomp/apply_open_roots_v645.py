#!/usr/bin/env python3
"""Enforce ELF-authenticated original IOS_Open allocator/flush ownership.

The allocator veneer is a tail call to a separate original root. The
general analyzer can otherwise absorb its callee or adjacent entry into
another emitted function. Preserve the original branch target and let
the native dispatcher transfer to the actual root.
"""
import argparse
from pathlib import Path
from make_v639_open_geometry import geometry,SPANS,exact_words
from make_private_elf_symbol_map import parse_functions
from apply_irq_bootstrap_v475 import rewrite
from apply_stm_native_open_v632 import OLD as SCANNER
from apply_bat_roots_v586 import ROOT,READ
FILE=Path('nWiiAnalyzer/src/analyzer.cpp')
IRQ_ROOTS=(0x805265ac,0x805265d4)
# Compile-only synthetic extents; owner builds derive exact sizes from ELF.
TEST_IRQ_SPANS=((IRQ_ROOTS[0],20),(IRQ_ROOTS[1],36))
def irq_spans(dol,elf):
    sizes=parse_functions(elf);out=[]
    for pc,limit in zip(IRQ_ROOTS,(0x805265c0,0x805265f8)):
        n=sizes.get(pc,0)
        if not 4<=n<=limit-pc or n&3:raise ValueError('IRQ helper extent')
        ws=exact_words(dol,elf,pc,n//4)
        if ws[-1]!=0x4e800020:raise ValueError('IRQ helper return')
        out.append((pc,n))
    return tuple(out)
def pairs(irq=TEST_IRQ_SPANS):
    spans=(*SPANS,*irq)
    if len(irq)!=2 or tuple(pc for pc,_ in irq)!=IRQ_ROOTS:raise ValueError('IRQ helper roots')
    if any(not 4<=n<=4096 or n&3 for pc,n in spans):raise ValueError('span extent')
    ordered=sorted(spans)
    if any(a+n>z for (a,n),(z,_) in zip(ordered,ordered[1:])):raise ValueError('span overlap')
    roots=ROOT+'''
    const auto open_owner=[](uint32_t a)->uint32_t {
'''+''.join(f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in spans)+'''      return 0;
    };
    if(open_owner(func_start)&&open_owner(func_start)!=func_start)continue;'''
    read='''        const auto open_root=open_owner(current_pc);
        if((open_root&&open_root!=func_start)||(open_owner(func_start)&&open_root!=func_start))break;
'''+READ
    # Only the authenticated original spans and the exact submit root
    # are in scope. Do not disable the general scanner.
    # Signature scanning occurs AFTER the function queue loop, outside
    # the local open_owner lambda's scope. Use exact root equality here.
    scan_roots='||'.join(f'func.start_address==0x{pc:08x}u' for pc in sorted({pc for pc,_ in spans}|{0x805195ec}))
    scanner=SCANNER+'\n    if('+scan_roots+')func.hle_hook_name.clear();'
    return ((ROOT,roots),(READ,read),(SCANNER,scanner))
def apply(root,irq=TEST_IRQ_SPANS):
    p=root/FILE
    if p.is_symlink():raise ValueError('symlink')
    s=p.read_text(encoding='utf-8');out=rewrite(s,pairs(irq))
    if s!=out:p.write_text(out,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        dol,elf=a.dol.read_bytes(),a.elf.read_bytes()
        geometry(dol,elf);apply(a.root,irq_spans(dol,elf))
    except (OSError,ValueError,UnicodeError):print('V645_OPEN_ANALYZER installed=0');return 1
    print('V645_OPEN_ANALYZER installed=1 roots=6 native_submit=1 exact_elf=1');return 0
if __name__=='__main__':raise SystemExit(main())
