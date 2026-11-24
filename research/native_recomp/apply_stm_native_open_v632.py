#!/usr/bin/env python3
"""Keep the authenticated IOS_Open root native in the bounded STM lane only."""
import argparse
from pathlib import Path
from prepare_v629_stm_open import geometry,OPEN
FILE=Path("nWiiAnalyzer/src/analyzer.cpp")
OLD="    func.hle_hook_name = scanner.match(opcodes);"
NEW=OLD+f"""
    // The bounded STM witness needs the original IOS_Open entry, not a hook.
    if (func.start_address == 0x{OPEN:08x}u) func.hle_hook_name.clear();"""
def rewrite(source):
    if source.count(NEW)==1 and source.count(OLD)==1:return source
    if source.count(OLD)!=1 or NEW in source:raise ValueError("scanner seam")
    return source.replace(OLD,NEW,1)
def main():
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);p.add_argument("dol",type=Path);p.add_argument("elf",type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>32*1024*1024 or a.elf.stat().st_size>64*1024*1024:raise ValueError("size")
        geometry(a.dol.read_bytes(),a.elf.read_bytes())
        f=a.root/FILE
        if f.is_symlink():raise ValueError("symlink")
        before=f.read_text(encoding="utf-8");after=rewrite(before)
        if before!=after:f.write_text(after,encoding="utf-8")
    except (OSError,ValueError):print("V632_STM_NATIVE_OPEN installed=0");return 1
    print("V632_STM_NATIVE_OPEN installed=1 scoped=1 authenticated=1");return 0
if __name__=="__main__":raise SystemExit(main())
