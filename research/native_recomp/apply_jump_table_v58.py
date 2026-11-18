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
# The initial data-pointer scan already marks all table entries as roots.
# Recover table-controlled edges regardless of that conservative root status.
OLD_ROOTS="""      if (known_functions.find(ptr) != known_functions.end()) {
          
          scan_addr += 4;
          continue;
      }"""
NEW_ROOTS="""      // A table entry may already be a candidate function root from
      // the data-pointer scan. It remains a valid computed branch edge.
      // Keep it in the caller's local blocks as well as its root entry."""
OLD_PARAM="const std::set<uint32_t> &known_functions) {"
NEW_PARAM="const std::set<uint32_t> & /*known_functions*/) {"

def rewrite(source):
    pairs=((OLD_SPR,NEW_SPR),(OLD_BCTR,NEW_BCTR),(OLD_ROOTS,NEW_ROOTS),(OLD_PARAM,NEW_PARAM))
    if all(source.count(new)==1 for old,new in pairs) and all(old not in source for old,new in pairs[1:]):
        return source
    if any(source.count(old)!=1 or new in source for old,new in pairs):
        raise ValueError("unexpected upstream PPC jump-table analyzer layout")
    for old,new in pairs:
        source=source.replace(old,new)
    return source
def apply(root):
    path=root/FILE
    source=path.read_text()
    fixed=rewrite(source)
    if fixed!=source:path.write_text(fixed)
    return fixed!=source
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("Patched PPC jump-table XO and swapped SPR fields:",apply(a.root))
