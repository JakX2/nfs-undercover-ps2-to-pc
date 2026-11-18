#!/usr/bin/env python3
"""Preserve single-instruction unconditional thunks to explicit native roots.

Do not split real internal branches, computed switch destinations, or
conservative data-pointer roots. No game-specific addresses are embedded.
"""
import argparse
from pathlib import Path
FILE=Path("nWiiAnalyzer/src/analyzer.cpp")
OLD_ROOTS="  std::set<uint32_t> known_functions;\n"
NEW_ROOTS="""  std::set<uint32_t> known_functions;
  const std::set<uint32_t> explicit_roots(additional_roots.begin(),
                                          additional_roots.end());
"""
OLD_BRANCH="""        } else if (inst.is_unconditional_branch()) {
          uint32_t target = inst.branch_target(current_pc);
          if (target != 0) {"""
NEW_BRANCH="""        } else if (inst.is_unconditional_branch()) {
          uint32_t target = inst.branch_target(current_pc);
          // A standalone tail thunk to an independently identified entry
          // must not absorb that entry's body or change its own start PC.
          if (current_pc == func_start && target != func_start &&
              explicit_roots.count(target) && known_functions.count(target))
            break;
          if (target != 0) {"""
def rewrite(source):
    pairs=((OLD_ROOTS,NEW_ROOTS),(OLD_BRANCH,NEW_BRANCH))
    if all(source.count(new)==1 for old,new in pairs):return source
    if any(source.count(old)!=1 or new in source for old,new in pairs):
        raise ValueError("unexpected explicit-root analyzer layout")
    for old,new in pairs:source=source.replace(old,new)
    return source
def apply(root):
    path=root/FILE
    source=path.read_text();new=rewrite(source)
    if new!=source:path.write_text(new)
    return new!=source
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("PASS: explicit-root tail thunk analyzer patch",apply(a.root))
