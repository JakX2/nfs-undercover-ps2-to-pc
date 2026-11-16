#!/usr/bin/env python3
"""Add Wii Gekko performance SPR value storage to the original-free NWiiRecomp runtime.

MMCR0 (952), MMCR1 (956), PMC1..4 (953,954,957,958) are exposed through
mtspr/mfspr. This intentionally models register values only, not hardware
counter events, MMCR control effects, exception triggers or wall-clock ticks.
The patch refuses unknown, partially-patched, or ambiguous upstream layouts.
"""
import argparse
from pathlib import Path

CTX = Path('nWiiRuntime/include/runtime/cpu_context.h')
RECOMP = Path('nWiiRecomp/src/recompiler.cpp')
IOS = Path('nWiiRuntime/src/hle/ios.cpp')

# Anchor the regular state and BackupState via one unique block per location.
CONTEXT_OLD = '  std::array<uint32_t, 4> sprg; \n\n  struct BackupState {'
CONTEXT_NEW = ('  std::array<uint32_t, 4> sprg; \n'
               '  uint32_t mmcr0 = 0;\n'
               '  uint32_t mmcr1 = 0;\n'
               '  std::array<uint32_t, 4> pmc{};\n\n  struct BackupState {')
BACKUP_OLD = '    std::array<uint32_t, 4> sprg;\n  };'
BACKUP_NEW = ('    std::array<uint32_t, 4> sprg;\n'
              '    uint32_t mmcr0 = 0;\n'
              '    uint32_t mmcr1 = 0;\n'
              '    std::array<uint32_t, 4> pmc{};\n  };')
READ_OLD = '''    } else if (spr == 1) {
      out << "    ctx.gpr[" << rD << "] = ctx.xer; // mfxer r" << rD << "\\n";
    } else if (spr >= 920 && spr <= 924) {'''
READ_NEW = '''    } else if (spr == 1) {
      out << "    ctx.gpr[" << rD << "] = ctx.xer; // mfxer r" << rD << "\\n";
    } else if (spr == 952 || spr == 956) {
      out << "    ctx.gpr[" << rD << "] = ctx." << (spr == 952 ? "mmcr0" : "mmcr1")
          << "; // mfspr performance control\\n";
    } else if (spr == 953 || spr == 954 || spr == 957 || spr == 958) {
      const unsigned index = (spr == 953 ? 0u : spr == 954 ? 1u : spr == 957 ? 2u : 3u);
      out << "    ctx.gpr[" << rD << "] = ctx.pmc[" << index
          << "]; // mfspr performance counter\\n";
    } else if (spr >= 920 && spr <= 924) {'''
WRITE_OLD = '''    } else if (spr == 1) {
      out << "    ctx.xer = ctx.gpr[" << rS << "]; // mtxer r" << rS << "\\n";
    } else {
      out << "    // unhandled mtspr " << spr'''
WRITE_NEW = '''    } else if (spr == 1) {
      out << "    ctx.xer = ctx.gpr[" << rS << "]; // mtxer r" << rS << "\\n";
    } else if (spr == 952 || spr == 956) {
      out << "    ctx." << (spr == 952 ? "mmcr0" : "mmcr1") << " = ctx.gpr["
          << rS << "]; // mtspr performance control\\n";
    } else if (spr == 953 || spr == 954 || spr == 957 || spr == 958) {
      const unsigned index = (spr == 953 ? 0u : spr == 954 ? 1u : spr == 957 ? 2u : 3u);
      out << "    ctx.pmc[" << index << "] = ctx.gpr[" << rS
          << "]; // mtspr performance counter\\n";
    } else {
      out << "    // unhandled mtspr " << spr'''
RESTORE_OLD = '           "                ctx.gqr = bk.gqr; ctx.sprg = bk.sprg;\\n";'
RESTORE_NEW = (RESTORE_OLD + '\n'
               '    out << "                ctx.mmcr0 = bk.mmcr0; ctx.mmcr1 = bk.mmcr1; ctx.pmc = bk.pmc;\\n";')
SAVE_OLD = '  bk.sprg = ctx.sprg;'
SAVE_NEW = SAVE_OLD + '\n  bk.mmcr0 = ctx.mmcr0; bk.mmcr1 = ctx.mmcr1; bk.pmc = ctx.pmc;'


def apply(root: Path):
    replacements = {
        CTX: [(CONTEXT_OLD, CONTEXT_NEW, 1), (BACKUP_OLD, BACKUP_NEW, 1)],
        RECOMP: [(READ_OLD, READ_NEW, 1), (WRITE_OLD, WRITE_NEW, 1),
                 (RESTORE_OLD, RESTORE_NEW, 2)],
        IOS: [(SAVE_OLD, SAVE_NEW, 2)],
    }
    updates = {}
    status = []
    for relative, edits in replacements.items():
        path = root / relative
        data = path.read_text(encoding='utf-8')
        next_data = data
        for old, new, count in edits:
            if next_data.count(new) == count and next_data.count(old) == (count if old in new else 0):
                status.append(True)
                continue
            if next_data.count(old) != count or next_data.count(new) != 0:
                raise ValueError(f'{relative}: missing, ambiguous or partial upstream patch')
            next_data = next_data.replace(old, new)
            status.append(False)
        updates[path] = next_data
    if any(status) and not all(status):
        raise ValueError('mixed patched/unpatched upstream: refuse partial modification')
    if all(status):
        return 'already applied'
    # All replacements validated before writing any file.
    for path, data in updates.items():
        path.write_text(data, encoding='utf-8')
    return 'installed'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('upstream', type=Path)
    args = ap.parse_args()
    print('V29 performance SPR state/emitter:', apply(args.upstream))
