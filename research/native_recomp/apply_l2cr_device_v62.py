#!/usr/bin/env python3
"""Opt-in L2CR *read source* for externally modeled hardware completion.

Default mfspr still returns CPUContext::l2cr unchanged. Test harnesses can
explicitly inject a callback to report L2IP (busy) transitions. This does
not provide a real Wii/Gekko L2 cache, clock, coherence, or completion model.
"""
import argparse
from pathlib import Path

CTX = Path('nWiiRuntime/include/runtime/cpu_context.h')
EMITTER = Path('nWiiRecomp/src/recompiler.cpp')
CHANGES = (
    (CTX, '  uint32_t l2cr = 0;\n\n  // Diagnostic guest cache-line ordering:',
          '  uint32_t l2cr = 0;\n'
          '  // Optional external status provider; unset by default. Never self-clears L2IP.\n'
          '  uint32_t (*l2cr_read_provider)(CPUContext&) = nullptr;\n'
          '  uint32_t guest_l2cr_read() {\n'
          '    return l2cr_read_provider ? l2cr_read_provider(*this) : l2cr;\n'
          '  }\n\n  // Diagnostic guest cache-line ordering:', 1),
    (EMITTER, 'ctx.l2cr; // mfspr L2CR value\\n',
              'ctx.guest_l2cr_read(); // mfspr L2CR, explicit external status\\n', 1),
)

def apply(root: Path) -> str:
    staged = {}
    state = []
    for file, old, new, count in CHANGES:
        content = (root/file).read_text(encoding='utf-8')
        nold, nnew = content.count(old), content.count(new)
        if nold==count and nnew==0:
            staged[file] = content.replace(old,new)
            state.append(False)
        elif nold==0 and nnew==count:
            staged[file]=content
            state.append(True)
        else:
            raise ValueError(f'V62 refuses unknown or partially patched {file}: old={nold}, new={nnew}')
    if any(state) and not all(state):
        raise ValueError('V62 refuses mixed original/updated sources')
    if all(state):return 'already applied'
    for file,contents in staged.items():
        (root/file).write_text(contents,encoding='utf-8')
    return 'installed'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('nwiirecomp_root',type=Path)
    a=p.parse_args();print('PASS: V62 explicit L2CR read provider',apply(a.nwiirecomp_root))
