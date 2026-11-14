#!/usr/bin/env python3
"""Bounded Wii L2CR guest-SPR model for owner-local NWiiRecomp.

The L2CR bit 31 is hardware read-only L2IP; when software starts a global
invalidate with L2I, test model returns in-progress for two polls then clears.
This is a deterministic cache-control handshake, NOT an actual host L2 cache.
"""
from pathlib import Path
import argparse

CONTEXT = 'nWiiRuntime/include/runtime/cpu_context.h'
EMITTER = 'nWiiRecomp/src/recompiler.cpp'
OLD_FIELD = '  uint32_t hid2 = 0; // Wii HID2, guest visible\n  uint32_t fpscr; '
NEW_FIELD = '''  uint32_t hid2 = 0; // Wii HID2, guest visible
  uint32_t l2cr = 0; // Wii Broadway L2 cache control (SPR1017)
  uint32_t l2cr_busy_polls = 0; // bounded deterministic L2IP hardware status
  uint32_t fpscr; '''
OLD_METHOD = '  // v19: FPSCR field-select write from lower 32 bits of a 64-bit FPR image.'
NEW_METHOD = '''  // Wii L2CR bits follow Broadway numbering: MSB=bit 0.
  // L2E=0x80000000, L2I=0x00200000; L2IP=0x00000001 is read-only.
  // Simulated completion handshake only: cache storage is not emulated.
  uint32_t read_l2cr() {
    const bool busy = l2cr_busy_polls != 0;
    if (busy) --l2cr_busy_polls;
    return (l2cr & ~1u) | (busy ? 1u : 0u);
  }
  void write_l2cr(uint32_t value) {
    constexpr uint32_t L2I = 0x00200000u;
    constexpr uint32_t L2E = 0x80000000u;
    const uint32_t old = l2cr;
    l2cr = value & ~1u; // L2IP cannot be written by PPC software
    // Invalidate requires L2 disabled. This is a test-level state model,
    // not a timing-accurate hardware simulation of Broadway's L2 cache.
    if ((l2cr & L2I) && !(old & L2I) && !(l2cr & L2E))
      l2cr_busy_polls = 2;
    else if (!(l2cr & L2I))
      l2cr_busy_polls = 0;
  }

  // v19: FPSCR field-select write from lower 32 bits of a 64-bit FPR image.'''
OLD_READ = '      out << "    ctx.gpr[" << rD << "] = 0; // mfspr L2CR\\n";'
NEW_READ = '      out << "    ctx.gpr[" << rD << "] = ctx.read_l2cr(); // mfspr L2CR\\n";'
OLD_WRITE = '    } else if (spr == 1008) {\n      out << "    ctx.hid0 = ctx.gpr[" << rS << "]; // mtspr HID0\\n";\n    } else {'
NEW_WRITE = '    } else if (spr == 1008) {\n      out << "    ctx.hid0 = ctx.gpr[" << rS << "]; // mtspr HID0\\n";\n    } else if (spr == 1017) {\n      out << "    ctx.write_l2cr(ctx.gpr[" << rS << "]); // mtspr L2CR\\n";\n    } else {'


def replace_once(text, before, after):
    if text.count(after) == 1:
        return text
    if text.count(before) != 1 or after in text:
        raise ValueError('unknown/conflicting NWiiRecomp source; refusing L2CR patch')
    return text.replace(before, after, 1)


def apply(root: Path):
    context_path, emitter_path = root / CONTEXT, root / EMITTER
    context, emitter = context_path.read_text(), emitter_path.read_text()
    next_context = replace_once(context, OLD_FIELD, NEW_FIELD)
    next_context = replace_once(next_context, OLD_METHOD, NEW_METHOD)
    next_emitter = replace_once(emitter, OLD_READ, NEW_READ)
    next_emitter = replace_once(next_emitter, OLD_WRITE, NEW_WRITE)
    # Entire patch validated before writing either source file.
    if next_context != context:
        context_path.write_text(next_context)
    if next_emitter != emitter:
        emitter_path.write_text(next_emitter)
    return next_context != context or next_emitter != emitter


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nwiirecomp_root', type=Path)
    args = parser.parse_args()
    print('Applied V20 Wii L2CR guest-SPR patch:', apply(args.nwiirecomp_root))
