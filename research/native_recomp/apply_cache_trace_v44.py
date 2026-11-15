#!/usr/bin/env python3
"""Increase bounded Wii guest cache-op diagnostic trace from V43 to V44.

The V43 event model stores the first 32 guest cache lines. Installing 15 Wii
exception handlers generates 75 flushes and 75 invalidations per startup.
V44 retains up to 256 addresses for validating repeated installation across
multiple calls. This is diagnostic state, NOT cache or JIT coherency.
Original-free, strict, idempotent and fail-closed on mixed versions.
"""
import argparse
from pathlib import Path

FILE = Path('nWiiRuntime/include/runtime/cpu_context.h')
OLD = ('std::array<uint32_t, 32> guest_flush_lines{};',
       'std::array<uint32_t, 32> guest_invalidate_lines{};')
NEW = ('std::array<uint32_t, 256> guest_flush_lines{};',
       'std::array<uint32_t, 256> guest_invalidate_lines{};')


def apply(root: Path) -> bool:
    path = root / FILE
    original = path.read_text(encoding='utf-8')
    states = []
    for old, new in zip(OLD, NEW):
        if original.count(old) == 1 and new not in original:
            states.append('old')
        elif original.count(new) == 1 and old not in original:
            states.append('new')
        else:
            raise ValueError('unknown/ambiguous Wii cache trace source revision')
    if len(set(states)) != 1:
        raise ValueError('partially upgraded Wii cache trace; refusing mixed state')
    if states[0] == 'new':
        return False
    updated = original
    for old, new in zip(OLD, NEW):
        updated = updated.replace(old, new, 1)
    path.write_text(updated, encoding='utf-8')
    return True


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('nwiirecomp_root',type=Path)
    args=ap.parse_args()
    print('V44 256-line guest cache trace patch:',
          'installed' if apply(args.nwiirecomp_root) else 'already installed')
