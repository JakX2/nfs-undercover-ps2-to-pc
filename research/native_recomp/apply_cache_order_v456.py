#!/usr/bin/env python3
"""Extend the flat-RAM cache runtime with dcbst/eieio host ordering.

No real cache residency, MMIO completion, writeback or AOT invalidation is
claimed. Install after V39/V43 cache events, with or without V44 capacity.
"""
import argparse
from pathlib import Path
from apply_cache_events_v43 import CONTEXT,EMITTER
CTX_OLD='''  void guest_sync() {
    ++guest_sync_count;'''
CTX_NEW='''  uint64_t guest_store_count = 0;
  uint64_t guest_eieio_count = 0;
  uint32_t guest_last_store = 0;
  void guest_dcbst(uint32_t effective_address) {
    guest_last_store = effective_address & ~31u;
    ++guest_store_count;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }
  void guest_eieio() {
    ++guest_eieio_count;
    std::atomic_thread_fence(std::memory_order_seq_cst);
  }
  void guest_sync() {
    ++guest_sync_count;'''
EMIT_OLD='''    } else if (xo == 854 || xo == 54 || xo == 278 || xo == 246 || xo == 470) {
      out << "    // unimplemented guest cache instruction\\n";'''
EMIT_NEW='''    } else if (xo == 54) {
      const std::string base = (rA == 0) ? "0u" : "ctx.gpr[" + std::to_string(rA) + "]";
      out << "    ctx.guest_dcbst(" << base << " + ctx.gpr[" << rB << "]);\\n";
    } else if (xo == 854) {
      out << "    ctx.guest_eieio(); // guest I/O ordering\\n";
    } else if (xo == 278 || xo == 246 || xo == 470) {
      out << "    // unimplemented guest cache instruction\\n";'''
def rewrite(c,e):
    if c.count(CTX_NEW)==1 and c.count(CTX_OLD)==1 and e.count(EMIT_NEW)==1 and EMIT_OLD not in e:
        return c,e,False
    if c.count(CTX_OLD)!=1 or CTX_NEW in c or 'guest_store_count' in c or 'guest_eieio_count' in c or e.count(EMIT_OLD)!=1 or EMIT_NEW in e:
        raise ValueError('unknown or mixed cache-order revision')
    nc=c.replace(CTX_OLD,CTX_NEW);ne=e.replace(EMIT_OLD,EMIT_NEW)
    if nc.replace(CTX_NEW,CTX_OLD)!=c or ne.replace(EMIT_NEW,EMIT_OLD)!=e:
        raise ValueError('roundtrip')
    return nc,ne,True
def apply(root):
    cp,ep=root/CONTEXT,root/EMITTER
    if cp.is_symlink() or ep.is_symlink():raise ValueError('symlink')
    c,e=cp.read_text(encoding='utf-8'),ep.read_text(encoding='utf-8')
    nc,ne,changed=rewrite(c,e)
    if changed:cp.write_text(nc,encoding='utf-8');ep.write_text(ne,encoding='utf-8')
    return changed
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V456_CACHE_ORDER installed=1 changed={int(apply(a.root))}')
