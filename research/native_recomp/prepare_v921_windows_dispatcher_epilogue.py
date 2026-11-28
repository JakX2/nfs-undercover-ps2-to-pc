#!/usr/bin/env python3
"""Read-only native full-image audit of the original dispatcher/RFI dependencies.

The V923 focused owner fixture already authenticates the original scheduler
and 54-word context-loader ending in RFI. This checks that the Windows
complete-image translator emitted those SAME original roots and direct edges.
It does not arm a runtime hook, synthesize interrupt state or execute RFI.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct

from prepare_v419_full_start import MAX_DOL
from prepare_v625_ipc_client import audit_native
from prepare_v667_si_dispatch import DISPATCH
from prepare_v680_si_helper import exact_function, verify_direct
from prepare_v709_os_leaves import owns_root
from prepare_owner_irq_join_v923 import plan
from prepare_owner_scheduler_v722 import E, S, reachable
from prepare_owner_context_v720 import L, RFI


def native_expectations(roots: dict[int, list[int]], resume: int,
                        disable: int, restore: int) -> dict[int, tuple[int, int]]:
    """Exclude the focused probe's synthetic guard and caller from real code."""
    if resume not in roots or len(roots[resume]) != 5 or roots[resume][-1] != 0x4e800020:
        raise ValueError('dispatcher shape')
    if L not in roots or len(roots[L]) != 54 or roots[L][-1] != RFI:
        raise ValueError('context loader')
    if len({resume, E, S, disable, restore, L}) != 6:
        raise ValueError('native overlap')
    expected = {resume + i * 4: (DISPATCH, word)
                for i, word in enumerate(roots[resume][:4])}
    for owner in (E, S, disable, restore):
        words = roots[owner]
        expected.update({pc: (owner, words[(pc-owner)//4])
                         for pc in reachable(owner, words)})
    expected.update({L + i * 4: (L, word)
                     for i, word in enumerate(roots[L])})
    if len(expected) < 70:
        raise ValueError('native coverage')
    return expected


def audit(dol: bytes, elf: bytes, generated: Path) -> int:
    if type(dol) is not bytes or type(elf) is not bytes or not isinstance(generated, Path):
        raise ValueError('input')
    if len(dol) > MAX_DOL or len(elf) > 64*1024*1024:
        raise ValueError('size')
    roots, j, _, _, _, _, d, r, _, enable_calls, *_ = plan(dol, elf)
    expected = native_expectations(roots, j, d, r)
    shards = sorted(generated.glob('output_*.cpp'))
    main = generated / 'main_output.cpp'
    if (len(shards) < 20 or not main.is_file() or main.is_symlink() or
            any(p.is_symlink() or not p.is_file() or p.stat().st_size > 64*1024*1024
                for p in (*shards, main))):
        raise ValueError('native tree')
    sources = [p.read_text(encoding='utf-8') for p in shards]
    outer = main.read_text(encoding='utf-8')
    count = audit_native(sources, outer, expected)
    for root, edges in ((DISPATCH, ((j, E), (j+4, S), (j+12, L))),
                        (E, enable_calls)):
        bodies = [exact_function(src, root) for src in sources if owns_root(src, root)]
        if len(bodies) != 1:
            raise ValueError('native owner')
        for site, dst in edges:
            verify_direct(bodies[0], site, dst)
    return count


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('dol', type=Path)
    p.add_argument('elf', type=Path)
    p.add_argument('generated', type=Path)
    a = p.parse_args()
    try:
        # Owner-only inputs stay on the private runner, never in the repository.
        count = audit(a.dol.read_bytes(), a.elf.read_bytes(), a.generated)
    except (OSError, ValueError, UnicodeError, IndexError, KeyError, struct.error):
        print('V921_WINDOWS_DISPATCHER_PREFLIGHT verified=0')
        return 1
    print(f'V921_WINDOWS_DISPATCHER_PREFLIGHT verified=1 native_labels={count} direct_edges=5 rfi_loader=1 execution=0 rfi=0 boot_verified=0')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
