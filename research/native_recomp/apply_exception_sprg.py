#!/usr/bin/env python3
"""Map PowerPC SPRG0-3 to the existing shared CPUContext scratch bank."""
import argparse
from pathlib import Path
EMIT=Path("nWiiRecomp/src/recompiler.cpp")
CTX=Path("nWiiRuntime/include/runtime/cpu_context.h")
READ='''    } else if (spr >= 912 && spr <= 919) {
      out << "    ctx.gpr[" << rD << "] = ctx.gqr[" << (spr - 912)'''
WRITE='''    } else if (spr >= 912 && spr <= 919) {
      out << "    ctx.gqr[" << (spr - 912) << "] = ctx.gpr[" << rS'''
READ_NEW='''    } else if (spr >= 272 && spr <= 275) {
      out << "    ctx.gpr[" << rD << "] = ctx.sprg[" << (spr - 272)
          << "]; // mfspr SPRG\\n";
'''+READ
WRITE_NEW='''    } else if (spr >= 272 && spr <= 275) {
      out << "    ctx.sprg[" << (spr - 272) << "] = ctx.gpr[" << rS
          << "]; // mtspr SPRG\\n";
'''+WRITE
OLD_INIT="srr1(0), gqr{0}, exception_pc(0)"
NEW_INIT="srr1(0), gqr{0}, sprg{0}, exception_pc(0)"
def rewrite(emit,ctx):
    for old,new in ((READ,READ_NEW),(WRITE,WRITE_NEW)):
        if emit.count(new)==1 and emit.count(old)==1:continue
        if emit.count(old)!=1 or new in emit:raise ValueError("unknown SPRG emitter layout")
        emit=emit.replace(old,new)
    if ctx.count(NEW_INIT)==1 and OLD_INIT not in ctx:pass
    elif ctx.count(OLD_INIT)==1 and NEW_INIT not in ctx:ctx=ctx.replace(OLD_INIT,NEW_INIT)
    else:raise ValueError("unknown SPRG constructor layout")
    return emit,ctx
def apply(root):
    e,c=root/EMIT,root/CTX;old=(e.read_text(),c.read_text());new=rewrite(*old)
    if old!=new:e.write_text(new[0]);c.write_text(new[1])
    return old!=new
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("PASS: PowerPC SPRG register bank",apply(a.root))
