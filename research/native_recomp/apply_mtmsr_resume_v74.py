#!/usr/bin/env python3
"""Explicit native dispatcher resume cases after interruptible mtmsr.

Both output modes already accept all internal labels in emit_function, but
their outer dispatchers omitted mtmsr continuation PCs. Add exact
instruction-boundary cases without altering instruction execution.
"""
import argparse
from pathlib import Path
FILE=Path("nWiiRecomp/src/recompiler.cpp")
OLD="          if (ppc_inst.is_branch_link() || ppc_inst.opcode() == 17) {"
NEW="""          const bool interrupt_resume =
              ppc_inst.opcode() == 31 && ppc_inst.extended_opcode() == 146 &&
              std::any_of(func.instructions.begin(), func.instructions.end(),
                          [&](const auto& next) { return next.address == inst.address + 4u; });
          if (ppc_inst.is_branch_link() || ppc_inst.opcode() == 17 ||
              interrupt_resume) {"""
def rewrite(src):
    if src.count(NEW)==2 and OLD not in src:return src
    if src.count(OLD)!=2 or NEW in src:raise ValueError("unexpected dispatcher resume layout")
    return src.replace(OLD,NEW)
def apply(root):
    path=root/FILE
    src=path.read_text();new=rewrite(src)
    if new!=src:path.write_text(new)
    return new!=src
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("PASS: explicit mtmsr resume dispatch",apply(a.root))
