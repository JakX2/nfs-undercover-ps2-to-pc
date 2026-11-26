#!/usr/bin/env python3
"""Compose native data-cache invalidation with the isolated V561 cache emitter.
Flat RAM and host fences, not a Wii cache-residency model.
"""
import argparse
from apply_cache_events_v43 import CONTEXT,EMITTER,EMIT_AFTER
from apply_cache_events_v561 import HID0
from apply_dcbi_v60 import OLD_CTX,NEW_CTX as BASE_CTX
from pathlib import Path
NEW_CTX=BASE_CTX.replace('  uint32_t guest_data_invalidate_count = 0;',
                         '  uint32_t guest_data_invalidate_count = 0;\n  uint32_t guest_last_data_invalidate = 0;').replace(
    '    ++guest_data_invalidate_count;','    ++guest_data_invalidate_count;\n    guest_last_data_invalidate = line;')
OLD_EMIT=EMIT_AFTER
NEW_EMIT=OLD_EMIT.replace('    } else if (xo == 854 || xo == 54 || xo == 278 || xo == 246 || xo == 470) {',
    '''    } else if (xo == 470) {
      const std::string base = (rA == 0) ? "0u" : "ctx.gpr[" + std::to_string(rA) + "]";
      out << "    ctx.guest_dcbi(" << base << " + ctx.gpr[" << rB << "]);\\n";
    } else if (xo == 854 || xo == 54 || xo == 278 || xo == 246) {''')
def rewrite(c,e):
    if c.count(HID0)!=1 or 'uint32_t hid4' in c or NEW_EMIT==OLD_EMIT:
        raise ValueError('isolated cache predecessor')
    if c.count(NEW_CTX)==1 and e.count(NEW_EMIT)==1 and OLD_EMIT not in e:
        if c.count('guest_data_invalidate_count = 0;')!=1 or e.count('ctx.guest_dcbi(')!=1:
            raise ValueError('duplicate isolated dcbi')
        return c,e,False
    if (c.count(OLD_CTX)!=1 or 'guest_data_invalidate_count' in c or
        e.count(OLD_EMIT)!=1 or 'ctx.guest_dcbi(' in e):
        raise ValueError('unknown or mixed isolated dcbi state')
    nc=c.replace(OLD_CTX,NEW_CTX,1);ne=e.replace(OLD_EMIT,NEW_EMIT,1)
    if nc.replace(NEW_CTX,OLD_CTX,1)!=c or ne.replace(NEW_EMIT,OLD_EMIT,1)!=e:
        raise ValueError('isolated dcbi roundtrip')
    return nc,ne,True
def apply(root):
    cp,ep=root/CONTEXT,root/EMITTER
    if cp.is_symlink() or ep.is_symlink():raise ValueError('symlink')
    c,e=cp.read_text(),ep.read_text()
    nc,ne,changed=rewrite(c,e)
    if changed:cp.write_text(nc);ep.write_text(ne)
    return changed
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    print(f'V1276_ISOLATED_DCBI installed=1 changed={int(apply(a.root))} flat_ram=1')
