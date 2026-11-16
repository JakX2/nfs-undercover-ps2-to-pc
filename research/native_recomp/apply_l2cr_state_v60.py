#!/usr/bin/env python3
"""Fail-closed, idempotent guest L2CR SPR value handling for NWiiRecomp.

This models *software-visible register values only*. It does not emulate
Gekko L2 invalidation/busy-bit transitions, write timing or cache contents.
"""
import argparse
from pathlib import Path

CTX = Path('nWiiRuntime/include/runtime/cpu_context.h')
EMITTER = Path('nWiiRecomp/src/recompiler.cpp')
IOS = Path('nWiiRuntime/src/hle/ios.cpp')

# Each tuple: relative file, original anchor, replacement, exact occurrence count.
EDITS = (
    (CTX, '  uint32_t hid0 = 0;\n  uint32_t hid4 = 0;\n',
          '  uint32_t hid0 = 0;\n  uint32_t hid4 = 0;\n  uint32_t l2cr = 0;\n', 1),
    (CTX, '    uint32_t hid0 = 0;\n    uint32_t hid4 = 0;\n',
          '    uint32_t hid0 = 0;\n    uint32_t hid4 = 0;\n    uint32_t l2cr = 0;\n', 1),
    (EMITTER, '      out << "    ctx.gpr[" << rD << "] = 0; // mfspr L2CR\\n";',
              '      out << "    ctx.gpr[" << rD << "] = ctx.l2cr; // mfspr L2CR value\\n";', 1),
    (EMITTER, '    } else if (spr == 1008 || spr == 1011) {\n      out << "    ctx." << (spr == 1008 ? "hid0" : "hid4") << " = ctx.gpr["\n          << rS << "]; // mtspr HID0/HID4\\n";\n    } else {',
              '    } else if (spr == 1008 || spr == 1011) {\n      out << "    ctx." << (spr == 1008 ? "hid0" : "hid4") << " = ctx.gpr["\n          << rS << "]; // mtspr HID0/HID4\\n";\n    } else if (spr == 1017) {\n      out << "    ctx.l2cr = ctx.gpr[" << rS << "]; // mtspr L2CR value\\n";\n    } else {', 1),
    (EMITTER, '    out << "                ctx.hid0 = bk.hid0; ctx.hid4 = bk.hid4;\\n";',
              '    out << "                ctx.hid0 = bk.hid0; ctx.hid4 = bk.hid4; ctx.l2cr = bk.l2cr;\\n";', 2),
    (IOS, '  bk.hid0 = ctx.hid0; bk.hid4 = ctx.hid4;',
          '  bk.hid0 = ctx.hid0; bk.hid4 = ctx.hid4; bk.l2cr = ctx.l2cr;', 2),
)


def apply(root: Path) -> str:
    originals = {}
    updates = {}
    states = []
    for filename, old, new, count in EDITS:
        if filename not in originals:
            originals[filename] = (root / filename).read_text(encoding='utf-8')
            updates[filename] = originals[filename]
        original = originals[filename]
        old_count, new_count = original.count(old), original.count(new)
        if old_count == count and new_count == 0:
            states.append(False)
            updates[filename] = updates[filename].replace(old, new)
        elif new_count == count and old_count == (count if old in new else 0):
            states.append(True)
        else:
            raise ValueError(f'V60 unknown or partial NWiiRecomp source: {filename} (old={old_count}, new={new_count})')
    if any(states) and not all(states):
        raise ValueError('V60 mixed new/old L2CR source refused without modification')
    if all(states):
        return 'already applied'
    # All edits validated before writing any changed file.
    for relative, updated in updates.items():
        (root / relative).write_text(updated, encoding='utf-8')
    return 'installed'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nwiirecomp_root', type=Path)
    args = parser.parse_args()
    print('PASS: V60 guest L2CR patch', apply(args.nwiirecomp_root))
