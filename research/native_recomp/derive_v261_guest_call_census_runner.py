#!/usr/bin/env python3
"""V261 original-native runner: summarize all 64 original post-IPC calls."""
import argparse
from pathlib import Path
from derive_v260_ipc_ppcmsg_boundary_runner import derive as previous

OLD = 'python3 "$V110_SOURCE_ROOT/derive_v260_ipc_ppcmsg_boundary_harness.py"'
NEW = 'python3 "$V110_SOURCE_ROOT/derive_v261_guest_call_census_harness.py"'
DONE = "echo 'V260_SC_POSTIPC_EVENT verified=1'"
APPEND = '''
# V260 must have reached its authenticated 64th guest call (not PPCMSG).
grep -Fqx 'V260_POSTIPC_RESULT kind=calls trials=16' "$work/v250-native.log"
# Parse 16 x 64 read-only PC/LR samples while keeping raw logs private.
python3 "$V110_SOURCE_ROOT/analyze_v261_postipc_calls.py" "$work/v250-native.log"
echo 'V261_CALL_CENSUS verified=1'
'''


def derive(source: str) -> str:
    s = previous(source)
    if s.count(OLD) != 1 or s.count(DONE) != 1:
        raise ValueError("V261 inherited V260 native runner changed")
    s = s.replace(OLD, NEW, 1)
    return s.replace(DONE, DONE + APPEND, 1)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    with a.output.open("x", encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
