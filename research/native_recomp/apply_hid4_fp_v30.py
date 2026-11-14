#!/usr/bin/env python3
"""Fail-closed original-free NWiiRecomp state for HID0/HID4 and mtfsb1/0.

Models guest-visible values only. HID0 speculation bit (0x200) and HID4 do
not acquire cycle, cache, MMU, or branch-prediction side effects; FPSCR bit
operations do not generate FP exceptions. Apply after V29 performance patch.
"""
import argparse
from pathlib import Path

CTX = Path('nWiiRuntime/include/runtime/cpu_context.h')
RECOMP = Path('nWiiRecomp/src/recompiler.cpp')
IOS = Path('nWiiRuntime/src/hle/ios.cpp')

CONTEXT_OLD = '  std::array<uint32_t, 4> pmc{};\n\n  struct BackupState {'
CONTEXT_NEW = ('  std::array<uint32_t, 4> pmc{};\n'
               '  uint32_t hid0 = 0;\n  uint32_t hid4 = 0;\n\n  struct BackupState {')
BACKUP_OLD = '    std::array<uint32_t, 4> pmc{};\n  };'
BACKUP_NEW = ('    std::array<uint32_t, 4> pmc{};\n'
              '    uint32_t hid0 = 0;\n    uint32_t hid4 = 0;\n  };')
READ_OLD = '''    } else if (spr == 1008) {
      out << "    ctx.gpr[" << rD << "] = 0; // mfspr HID0 (stub)\\n";
    } else if (spr == 287) {'''
READ_NEW = '''    } else if (spr == 1008 || spr == 1011) {
      out << "    ctx.gpr[" << rD << "] = ctx." << (spr == 1008 ? "hid0" : "hid4")
          << "; // mfspr HID0/HID4\\n";
    } else if (spr == 287) {'''
WRITE_OLD = '''    } else {
      out << "    // unhandled mtspr " << spr
          << "\\n"; 
    }
  } else if (ppc_inst.opcode() == 31 && ppc_inst.extended_opcode() == 0) {'''
WRITE_NEW = '''    } else if (spr == 1008 || spr == 1011) {
      out << "    ctx." << (spr == 1008 ? "hid0" : "hid4") << " = ctx.gpr["
          << rS << "]; // mtspr HID0/HID4\\n";
    } else {
      out << "    // unhandled mtspr " << spr
          << "\\n"; 
    }
  } else if (ppc_inst.opcode() == 31 && ppc_inst.extended_opcode() == 0) {'''
FPSCR_OLD = '''    } else if (xo == 38 ||
               xo == 70) { 
      out << "    // mtfsb1/mtfsb0 stub (FPSCR ignored)\\n";
    } else if (xo == 64) { '''
FPSCR_NEW = '''    } else if (xo == 38 || xo == 70) {
      const uint32_t bit = (ppc_inst.value() >> 21) & 31u;
      const uint32_t mask = 1u << (31u - bit);
      if (xo == 38)
        out << "    ctx.fpscr |= 0x" << std::hex << mask << std::dec
            << "; // mtfsb1 selected FPSCR bit\\n";
      else
        out << "    ctx.fpscr &= ~0x" << std::hex << mask << std::dec
            << "; // mtfsb0 selected FPSCR bit\\n";
    } else if (xo == 64) { '''
RESTORE_OLD = '    out << "                ctx.mmcr0 = bk.mmcr0; ctx.mmcr1 = bk.mmcr1; ctx.pmc = bk.pmc;\\n";'
RESTORE_NEW = RESTORE_OLD + '\n    out << "                ctx.hid0 = bk.hid0; ctx.hid4 = bk.hid4;\\n";'
SAVE_OLD = '  bk.mmcr0 = ctx.mmcr0; bk.mmcr1 = ctx.mmcr1; bk.pmc = ctx.pmc;'
SAVE_NEW = SAVE_OLD + '\n  bk.hid0 = ctx.hid0; bk.hid4 = ctx.hid4;'

EDITS = {
    CTX: [(CONTEXT_OLD, CONTEXT_NEW, 1), (BACKUP_OLD, BACKUP_NEW, 1)],
    RECOMP: [(READ_OLD, READ_NEW, 1), (WRITE_OLD, WRITE_NEW, 1),
             (FPSCR_OLD, FPSCR_NEW, 1), (RESTORE_OLD, RESTORE_NEW, 2)],
    IOS: [(SAVE_OLD, SAVE_NEW, 2)],
}


def apply(root: Path):
    updates = {}
    states = []
    for relative, replacements in EDITS.items():
        path = root / relative
        current = path.read_text(encoding='utf-8')
        updated = current
        for old, new, count in replacements:
            if updated.count(new) == count and updated.count(old) == (count if old in new else 0):
                states.append(True)
                continue
            if updated.count(old) != count or updated.count(new) != 0:
                raise ValueError(f'{relative}: unknown, ambiguous, or partially patched NWiiRecomp')
            updated = updated.replace(old, new)
            states.append(False)
        updates[path] = updated
    if any(states) and not all(states):
        raise ValueError('mixed partially patched source refused atomically')
    if all(states):
        return 'already applied'
    for path, updated in updates.items():
        path.write_text(updated, encoding='utf-8')
    return 'installed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nwiirecomp_root', type=Path)
    args = parser.parse_args()
    print('V30 HID0/HID4/FPSCR:', apply(args.nwiirecomp_root))
