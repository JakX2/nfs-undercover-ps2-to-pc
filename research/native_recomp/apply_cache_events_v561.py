#!/usr/bin/env python3
"""Install the shared V43 cache trace in the isolated V18 HID0 runtime.

The SC harness does not install the continuous HID4/performance-register
chain. Reuse the exact V43 emitter transformations and cache methods, but
anchor their state at the pinned upstream SPRG/BackupState boundary.
No original game code or bytes are used.
"""
import argparse
from pathlib import Path
from apply_cache_events_v43 import (
    CONTEXT, EMITTER, CTX_AFTER as SHARED_CONTEXT,
    EMIT_BEFORE, EMIT_AFTER, ISYNC_BEFORE, ISYNC_AFTER, transform,
)

HID0 = '  uint32_t hid0 = 0; // Wii HID0, guest visible\n'
BASE = '  std::array<uint32_t, 4> sprg; \n\n'
CTX_BEFORE = BASE + '  struct BackupState {'
CTX_AFTER = BASE + SHARED_CONTEXT.split('\n\n', 1)[1]


def rewrite(ctx, emitter):
    if ctx.count(HID0) != 1 or 'uint32_t hid4' in ctx:
        raise ValueError('SC cache patch requires isolated V18 HID0 state')
    def state(source, old, new):
        if source.count(old) == 1 and new not in source:
            return False
        if source.count(new) == 1 and old not in source:
            return True
        raise ValueError('unknown or ambiguous isolated cache anchor')
    states = (
        state(ctx, CTX_BEFORE, CTX_AFTER),
        state(emitter, EMIT_BEFORE, EMIT_AFTER),
        state(emitter, ISYNC_BEFORE, ISYNC_AFTER),
    )
    if len(set(states)) != 1:
        raise ValueError('mixed isolated cache patch state')
    if states[0]:
        return ctx, emitter
    if 'guest_sync_count' in ctx or 'guest_isync_count' in ctx:
        raise ValueError('conflicting cache state')
    nc = transform(ctx, [(CTX_BEFORE, CTX_AFTER)])
    ne = transform(emitter, [(EMIT_BEFORE, EMIT_AFTER),
                             (ISYNC_BEFORE, ISYNC_AFTER)])
    if (nc.replace(CTX_AFTER, CTX_BEFORE) != ctx or
            ne.replace(EMIT_AFTER, EMIT_BEFORE).replace(ISYNC_AFTER, ISYNC_BEFORE) != emitter):
        raise ValueError('isolated cache patch roundtrip')
    return nc, ne


def apply(root):
    cp, ep = root / CONTEXT, root / EMITTER
    if cp.is_symlink() or ep.is_symlink():
        raise ValueError('source symlink')
    ctx, emitter = cp.read_text(), ep.read_text()
    nc, ne = rewrite(ctx, emitter)
    if (nc, ne) == (ctx, emitter):
        return False
    # Validate idempotence and reject mixed/duplicate states before writing.
    if rewrite(nc, ne) != (nc, ne):
        raise ValueError('isolated cache patch not idempotent')
    for c, e in ((nc, emitter), (ctx, ne), (ctx + CTX_BEFORE, emitter),
                 (ctx.replace(HID0, ''), emitter)):
        try:
            rewrite(c, e)
        except ValueError:
            continue
        raise ValueError('isolated cache negative control accepted')
    cp.write_text(nc)
    ep.write_text(ne)
    return True


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('root', type=Path)
    args = p.parse_args()
    print('V566 isolated SC cache patch: installed=1 changed=' + str(int(apply(args.root))))
