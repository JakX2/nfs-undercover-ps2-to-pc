#!/usr/bin/env python3
"""Enforce ELF-authenticated original IOS_Open allocator/flush ownership.

The allocator veneer is a tail call to a separate original root. The
general analyzer can otherwise absorb its callee or adjacent entry into
another emitted function. Preserve the original branch target and let
the native dispatcher transfer to the actual root.
"""
import argparse
from pathlib import Path
from make_v639_open_geometry import geometry,SPANS
from apply_irq_bootstrap_v475 import rewrite
from apply_stm_native_open_v632 import OLD as SCANNER
from apply_bat_roots_v586 import ROOT,READ
FILE=Path('nWiiAnalyzer/src/analyzer.cpp')
def pairs():
    roots=ROOT+'''
    const auto open_owner=[](uint32_t a)->uint32_t {
'''+''.join(f'      if(a>=0x{pc:08x}u&&a<0x{pc+n:08x}u)return 0x{pc:08x}u;\n' for pc,n in SPANS)+'''      return 0;
    };
    if(open_owner(func_start)&&open_owner(func_start)!=func_start)continue;'''
    read='''        const auto open_root=open_owner(current_pc);
        if((open_root&&open_root!=func_start)||(open_owner(func_start)&&open_root!=func_start))break;
'''+READ
    # Only the authenticated original spans and the exact submit root
    # are in scope. Do not disable the general scanner.
    # Signature scanning occurs AFTER the function queue loop, outside
    # the local open_owner lambda's scope. Use exact root equality here.
    scan_roots='||'.join(f'func.start_address==0x{pc:08x}u' for pc in sorted({pc for pc,_ in SPANS}|{0x805195ec}))
    scanner=SCANNER+'\n    if('+scan_roots+')func.hle_hook_name.clear();'
    return ((ROOT,roots),(READ,read),(SCANNER,scanner))
def apply(root):
    p=root/FILE
    if p.is_symlink():raise ValueError('symlink')
    s=p.read_text(encoding='utf-8');out=rewrite(s,pairs())
    if s!=out:p.write_text(out,encoding='utf-8')
def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        geometry(a.dol.read_bytes(),a.elf.read_bytes());apply(a.root)
    except (OSError,ValueError,UnicodeError):print('V645_OPEN_ANALYZER installed=0');return 1
    print('V645_OPEN_ANALYZER installed=1 roots=4 native_submit=1 exact_elf=1');return 0
if __name__=='__main__':raise SystemExit(main())
