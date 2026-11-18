#!/usr/bin/env python3
"""Original-free native flat-RAM dcbz semantics, separate from dcbz_l."""
import argparse
from pathlib import Path
CONTEXT=Path("nWiiRuntime/include/runtime/cpu_context.h")
EMITTER=Path("nWiiRecomp/src/recompiler.cpp")
HEADER=CONTEXT.parent/"flat_cacheline_zero_v67.h"
OLD_INCLUDE="#include <stack>"
NEW_INCLUDE=OLD_INCLUDE+'\n#include "flat_cacheline_zero_v67.h"'
OLD_CTX="  MMU mmu;"
NEW_CTX=OLD_CTX+"""
  FlatCachelineZeroTrace guest_dcbz_trace;
  void guest_dcbz(uint32_t ea) { guest_dcbz_trace.zero(mmu,ea); }"""
OLD_EMIT='      out << "    // dcbz (data cache block zero) - stub\\n";'
NEW_EMIT='''      const std::string base = rA==0 ? "0u" : "ctx.gpr[" + std::to_string(rA) + "]";
      out << "    ctx.guest_dcbz(" << base << " + ctx.gpr[" << rB << "]);\\n";'''
def rewrite(c,e):
    edits=((OLD_INCLUDE,NEW_INCLUDE),(OLD_CTX,NEW_CTX))
    states=[]
    for old,new in edits:
        if c.count(new)==1 and c.count(old)==1:states.append(True);continue
        if c.count(old)!=1 or new in c:raise ValueError("unknown dcbz context revision")
        c=c.replace(old,new);states.append(False)
    if e.count(NEW_EMIT)==1 and OLD_EMIT not in e:states.append(True)
    elif e.count(OLD_EMIT)==1 and NEW_EMIT not in e:
        e=e.replace(OLD_EMIT,NEW_EMIT);states.append(False)
    else:raise ValueError("unknown dcbz emitter revision")
    if any(states) and not all(states):raise ValueError("mixed dcbz patch state")
    return c,e,all(states)
def apply(root):
    cp,ep,hp=root/CONTEXT,root/EMITTER,root/HEADER
    c,e=cp.read_text(),ep.read_text();nc,ne,done=rewrite(c,e)
    header=Path(__file__).with_name(HEADER.name).read_text()
    if hp.exists() and hp.read_text()!=header:raise ValueError("unexpected existing dcbz helper")
    if done:
        if not hp.is_file():raise ValueError("dcbz context references missing helper")
        return False
    if hp.exists():raise ValueError("partial dcbz helper installation")
    hp.write_text(header);cp.write_text(nc);ep.write_text(ne)
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("V67 flat-RAM dcbz patch:",apply(a.root))
