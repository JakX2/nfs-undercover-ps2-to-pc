#!/usr/bin/env python3
"""V263: retain verified V262 guest execution, report only callsite aggregates."""
import argparse
from pathlib import Path
from derive_v262_ipc_state_runner import derive as previous

DONE = "echo 'V262_IPC_STATE verified=1'"
EXTRA = '''
python3 "$V110_SOURCE_ROOT/analyze_v263_hotspot.py" "$work/v250-native.log"
echo 'V263_HOTSPOT verified=1'
'''

def derive(source: str) -> str:
    s = previous(source)
    if s.count(DONE) != 1:
        raise ValueError("V263 verified V262 owner-native runner changed")
    return s.replace(DONE, DONE + EXTRA, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.output.open("x", encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
