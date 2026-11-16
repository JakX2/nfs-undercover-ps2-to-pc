#!/usr/bin/env python3
"""Original-free V43 cache emitter-state patch fail-closed/idempotence tests."""
import argparse
import tempfile
from pathlib import Path
from apply_cache_events_v43 import (
    apply, CTX_BEFORE, CTX_AFTER,
    EMIT_BEFORE, EMIT_AFTER, ISYNC_BEFORE, ISYNC_AFTER,
    CONTEXT, EMITTER,
)


def verify(root: Path, context: str, emitter: str, expected_ok: bool):
    cpath, epath = root / CONTEXT, root / EMITTER
    cpath.parent.mkdir(parents=True, exist_ok=True)
    epath.parent.mkdir(parents=True, exist_ok=True)
    cpath.write_text(context, encoding='utf-8')
    epath.write_text(emitter, encoding='utf-8')
    try:
        changed = apply(root)
    except ValueError:
        if expected_ok:
            raise
        assert cpath.read_text()==context and epath.read_text()==emitter, 'partial write on failed patch'
        return False
    if not expected_ok:
        raise AssertionError('invalid cache patch input was accepted')
    assert changed
    assert cpath.read_text()==CTX_AFTER
    assert epath.read_text()==EMIT_AFTER+'\n'+ISYNC_AFTER
    assert not apply(root), 'V43 patch is not idempotent'
    return True


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('nwiirecomp_root', type=Path)
    a=ap.parse_args()
    root=a.nwiirecomp_root
    c=(root / CONTEXT).read_text(encoding='utf-8')
    e=(root / EMITTER).read_text(encoding='utf-8')
    assert c.count(CTX_AFTER)==1 and e.count(EMIT_AFTER)==1 and e.count(ISYNC_AFTER)==1, 'installed patch missing or ambiguous'
    assert not apply(root), 'V43 was not idempotent on the genuine NWiiRecomp checkout'
    count=2
    with tempfile.TemporaryDirectory(prefix='v43_patch_guard_') as tmp:
        t=Path(tmp)
        assert verify(t, CTX_BEFORE, EMIT_BEFORE+'\n'+ISYNC_BEFORE, True)
        count+=2
        bad_inputs=[
            (CTX_BEFORE+'\n'+CTX_BEFORE, EMIT_BEFORE+'\n'+ISYNC_BEFORE),
            (CTX_BEFORE[:-1],EMIT_BEFORE+'\n'+ISYNC_BEFORE),
            (CTX_BEFORE,EMIT_BEFORE+'\n'+EMIT_BEFORE+'\n'+ISYNC_BEFORE),
            (CTX_BEFORE,EMIT_BEFORE+'\n'+ISYNC_BEFORE+'\n'+ISYNC_BEFORE),
            (CTX_BEFORE,EMIT_BEFORE+'\n'+ISYNC_BEFORE[:-1]),
            (CTX_AFTER,EMIT_BEFORE+'\n'+ISYNC_BEFORE),
            (CTX_BEFORE,EMIT_AFTER+'\n'+ISYNC_AFTER),
            (CTX_AFTER,EMIT_AFTER+'\n'+ISYNC_BEFORE),
            (CTX_BEFORE,EMIT_AFTER+'\n'+ISYNC_BEFORE),
            (CTX_AFTER,EMIT_BEFORE+'\n'+ISYNC_AFTER),
        ]
        for i,(ctx,em) in enumerate(bad_inputs):
            verify(t,ctx,em,False)
            count+=1
    print(f'PASS: {count} V43 source-only cache patch idempotence and fail-closed checks')

if __name__ == '__main__':
    main()
