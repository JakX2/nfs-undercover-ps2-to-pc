#!/usr/bin/env python3
"""Independent Wii HID0/HID2 guest-state adaptation for an owner-local NWiiRecomp checkout.

Preserves existing source and refuses unknown upstream revisions; does not run or
redistribute original game code. Scoped to HID0 (SPR1008) / HID2 (SPR920).
"""
import argparse
from pathlib import Path

CONTEXT = 'nWiiRuntime/include/runtime/cpu_context.h'
RECOMPILER = 'nWiiRecomp/src/recompiler.cpp'

CTX_BEFORE = '  uint32_t msr;   \n  uint32_t fpscr; '
CTX_AFTER = '  uint32_t msr;   \n  uint32_t hid0 = 0; // Wii HID0, guest visible\n  uint32_t hid2 = 0; // Wii HID2, guest visible\n  uint32_t fpscr; '
READ_BEFORE = '''} else if (spr >= 920 && spr <= 924) {
      out << "    ctx.gpr[" << rD << "] = 0; // mfspr HID " << spr << "\\n";
    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = 0; // mfspr HID0 (stub)\\n";
    } else if (spr == 287) {'''
READ_AFTER = '''} else if (spr == 920) {
      out << "    ctx.gpr[" << rD << "] = ctx.hid2; // mfspr HID2\\n";
    } else if (spr >= 921 && spr <= 924) {
      out << "    ctx.gpr[" << rD << "] = 0; // other HID SPR not implemented: " << spr << "\\n";
    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = ctx.hid0; // mfspr HID0\\n";
    } else if (spr == 287) {'''
WRITE_BEFORE = '''} else {
      out << "    // unhandled mtspr " << spr
          << "\\n"; 
    }
  } else if (ppc_inst.opcode() == 31 && ppc_inst.extended_opcode() == 0) {'''
WRITE_AFTER = '''} else if (spr == 920) {
      out << "    ctx.hid2 = ctx.gpr[" << rS << "]; // mtspr HID2\\n";
    } else if (spr == 1008) {
      out << "    ctx.hid0 = ctx.gpr[" << rS << "]; // mtspr HID0\\n";
    } else {
      out << "    // unhandled mtspr " << spr
          << "\\n"; 
    }
  } else if (ppc_inst.opcode() == 31 && ppc_inst.extended_opcode() == 0) {'''


def transform(old: str, replacements):
    result = old
    for before, after in replacements:
        if result.count(after) == 1:
            continue  # exact already-patched path
        if result.count(before) != 1 or result.count(after) != 0:
            raise ValueError('unknown or conflicting upstream source; refusing patch')
        result = result.replace(before, after, 1)
    return result


def apply(root: Path) -> bool:
    path_ctx, path_recomp = root / CONTEXT, root / RECOMPILER
    old_ctx = path_ctx.read_text(encoding='utf-8')
    old_recomp = path_recomp.read_text(encoding='utf-8')
    next_ctx = transform(old_ctx, [(CTX_BEFORE, CTX_AFTER)])
    next_recomp = transform(old_recomp, [(READ_BEFORE, READ_AFTER), (WRITE_BEFORE, WRITE_AFTER)])
    # All transforms validated before the first write.
    if old_ctx != next_ctx:
        path_ctx.write_text(next_ctx, encoding='utf-8')
    if old_recomp != next_recomp:
        path_recomp.write_text(next_recomp, encoding='utf-8')
    return old_ctx != next_ctx or old_recomp != next_recomp


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('nwiirecomp_root', type=Path)
    a = p.parse_args()
    print('Applied original-free HID0/HID2 patch:', apply(a.nwiirecomp_root))
