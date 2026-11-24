#!/usr/bin/env python3
"""Native dcbi trace and host fence composed after V456 full-image cache patches.

Flat RAM does not simulate cache residency or writeback. Data invalidation
must not zero memory, mutate registers, or invalidate generated host code.
"""
import argparse
from pathlib import Path
from apply_cache_events_v43 import CONTEXT,EMITTER
from apply_cache_order_v456 import CTX_NEW as ORDER_CTX,EMIT_NEW as ORDER_EMIT
from apply_dcbi_v60 import OLD_CTX,NEW_CTX
EMIT_NEW=ORDER_EMIT.replace(
    '    } else if (xo == 278 || xo == 246 || xo == 470) {',
    '''    } else if (xo == 470) {
      const std::string base = (rA == 0) ? "0u" : "ctx.gpr[" + std::to_string(rA) + "]";
      out << "    ctx.guest_dcbi(" << base << " + ctx.gpr[" << rB << "]);\\n";
    } else if (xo == 278 || xo == 246) {''')
def rewrite(c,e):
    if c.count(ORDER_CTX)!=1 or EMIT_NEW==ORDER_EMIT:raise ValueError('V456 predecessor')
    if c.count(NEW_CTX)==1 and e.count(EMIT_NEW)==1 and ORDER_EMIT not in e:return c,e,False
    if c.count(OLD_CTX)!=1 or NEW_CTX in c or 'guest_data_invalidate_count' in c or e.count(ORDER_EMIT)!=1 or EMIT_NEW in e or 'ctx.guest_dcbi(' in e:
        raise ValueError('unknown or mixed dcbi composition')
    nc=c.replace(OLD_CTX,NEW_CTX,1);ne=e.replace(ORDER_EMIT,EMIT_NEW,1)
    if nc.replace(NEW_CTX,OLD_CTX,1)!=c or ne.replace(EMIT_NEW,ORDER_EMIT,1)!=e:raise ValueError('roundtrip')
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
    print(f'V532_DCBI installed=1 changed={int(apply(a.root))} flat_ram=1')
