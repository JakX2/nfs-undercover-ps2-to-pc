#!/usr/bin/env python3
"""Source-only installer regression, no proprietary assets needed."""
import tempfile
from pathlib import Path
from install_ea_codecs_v11 import install

with tempfile.TemporaryDirectory() as name:
    root = Path(name)
    destination = root / 'nWiiRuntime/include/runtime'
    destination.mkdir(parents=True)
    sources = Path(__file__).resolve().parent
    try:
        install(root, sources)
        raise AssertionError('missing V10 dependency did not fail')
    except ValueError:
        pass
    (destination / 'jdlz_decoder_v10.h').write_bytes((sources / 'jdlz_decoder_v10.h').read_bytes())
    assert install(root, sources) == 2
    assert install(root, sources) == 0
    target = destination / 'huff_decoder_v11.h'
    target.write_text('not our header')
    try:
        install(root, sources)
        raise AssertionError('conflicting header was overwritten')
    except ValueError:
        assert target.read_text() == 'not our header'
print('PASS: V11 runtime header installer prerequisites, idempotence and conflict safety')
