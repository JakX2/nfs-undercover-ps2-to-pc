#!/usr/bin/env python3
"""Original-free extension of Wii MMU hardware address aperture to Hollywood."""
import argparse
from pathlib import Path
FILE=Path("nWiiRuntime/include/runtime/cpu_context.h")
OLD="(paddr >= 0x0D000000 && paddr < 0x0D010000);"
NEW="""(paddr >= 0x0D000000 && paddr < 0x0D010000) ||
             (paddr >= 0x0D800000 && paddr < 0x0D810000);"""
def rewrite(source):
    if source.count(NEW)==1 and OLD not in source:return source
    if source.count(OLD)!=1 or NEW in source:raise ValueError("unknown upstream MMIO aperture")
    return source.replace(OLD,NEW)
def apply(root):
    p=root/FILE;s=p.read_text();t=rewrite(s)
    if s!=t:p.write_text(t)
    return s!=t
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("V62 Hollywood address aperture:",apply(a.root))
