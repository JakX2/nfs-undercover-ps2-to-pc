#!/usr/bin/env python3
"""Original-free diagnostic data-cache invalidation and host ordering."""
import argparse
from pathlib import Path
from apply_cache_events_v43 import CONTEXT,EMITTER

OLD_CTX="  void guest_dcbf(uint32_t effective_address) {"
NEW_CTX="""  std::array<uint32_t, 256> guest_data_invalidate_lines{};
  uint32_t guest_data_invalidate_count = 0;

  void guest_dcbi(uint32_t effective_address) {
    const uint32_t line = effective_address & ~31u;
    if (guest_data_invalidate_count < guest_data_invalidate_lines.size())
      guest_data_invalidate_lines[guest_data_invalidate_count] = line;
    ++guest_data_invalidate_count;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }

  void guest_dcbf(uint32_t effective_address) {"""
OLD_EMIT="    if (xo == 86 || xo == 982) {"
NEW_EMIT="""    if (xo == 470) {
      const std::string base = (rA == 0) ? "0u" : "ctx.gpr[" + std::to_string(rA) + "]";
      out << "    ctx.guest_dcbi(" << base << " + ctx.gpr[" << rB << "]);\\n";
    } else
    if (xo == 86 || xo == 982) {"""

def apply(root):
    cp,ep=root/CONTEXT,root/EMITTER
    c,e=cp.read_text(),ep.read_text()
    if c.count(NEW_CTX)==1 and e.count(NEW_EMIT)==1:return False
    if NEW_CTX in c or NEW_EMIT in e or c.count(OLD_CTX)!=1 or e.count(OLD_EMIT)!=1:
        raise ValueError("unexpected or mixed data-cache invalidation patch state")
    cp.write_text(c.replace(OLD_CTX,NEW_CTX));ep.write_text(e.replace(OLD_EMIT,NEW_EMIT))
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("root",type=Path);a=p.parse_args()
    print("V60 data-cache invalidation trace patch:",apply(a.root))
