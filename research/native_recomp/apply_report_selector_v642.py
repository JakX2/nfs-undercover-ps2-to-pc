#!/usr/bin/env python3
"""Scoped native local jump table for the isolated console selector."""
import argparse
from pathlib import Path
from apply_report_table_v594 import pairs
from apply_irq_bootstrap_v475 import rewrite
from make_v594_boot_report_geometry import geometry
def apply(root,bctr):
    p=root/'nWiiAnalyzer/src/analyzer.cpp'
    # Keep the authenticated table checks and change only the root/span
    # guard for this independent partial-function fixture.
    rules=tuple((a,z.replace('0x805203c4u','0x80520410u').replace('0x80520670u','0x8052055cu')) for a,z in pairs(bctr))
    s=p.read_text();p.write_text(rewrite(s,rules))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        bctr,_=geometry(a.dol.read_bytes(),a.elf.read_bytes());apply(a.root,bctr)
    except (OSError,ValueError):print('V642_REPORT_ANALYZER installed=0');raise SystemExit(1)
    print('V642_REPORT_ANALYZER installed=1')
