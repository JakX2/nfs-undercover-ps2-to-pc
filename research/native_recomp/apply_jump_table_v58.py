#!/usr/bin/env python3
"""Original-free PPC opcode-field fix for NWiiRecomp jump-table discovery."""
import argparse
from pathlib import Path
FILE=Path("nWiiAnalyzer/src/analyzer.cpp")
OLD_SPR="uint32_t spr = (inst.value() >> 11) & 0x3FF;"
NEW_SPR="""uint32_t spr = (inst.value() >> 11) & 0x3FF;
      spr = ((spr & 0x1F) << 5) | (spr >> 5);"""
OLD_BCTR="if (inst.opcode() == 19 && (inst.value() & 0x3FF) == 528) {"
NEW_BCTR="if (inst.opcode() == 19 && inst.extended_opcode() == 528) {"
def rewrite(source):
    if source.count(NEW_SPR)==1 and source.count(NEW_BCTR)==1 and OLD_BCTR not in source:
        return source
    if source.count(OLD_SPR)!=1 or source.count(OLD_BCTR)!=1 or NEW_SPR in source or NEW_BCTR in source:
        raise ValueError("unexpected upstream PPC jump-table analyzer layout")
    return source.replace(OLD_SPR,NEW_SPR).replace(OLD_BCTR,NEW_BCTR)
def apply(root):
    path=root/FILE
    source=path.read_text()
    fixed=rewrite(source)
    if fixed!=source:path.write_text(fixed)
    return fixed!=source
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("Patched PPC jump-table XO and swapped SPR fields:",apply(a.root))
