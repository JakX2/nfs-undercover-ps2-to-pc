#!/usr/bin/env python3
"""V138 classify owner-original pending IOS request without ticking the bus."""
import argparse
from pathlib import Path
from derive_v137_ios_liveness_runner import derive as previous

BEFORE = 'python3 "$here/derive_v137_ios_liveness_harness.py"'
AFTER = 'python3 "$here/derive_v138_ios_request_harness.py"'
FAIL = "  echo 'V130_NATIVE_EXIT ok=0'"
DONE = "echo 'V137_IOS_PROBE verified=1'"
PATTERN = r'^V138_IOS_REQUEST valid=[01] command=[0-9]{1,10} path_kind=[0-7] mode=[0-9]{1,10}$'

def derive(source: str) -> str:
    s=previous(source)
    if s.count(BEFORE)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V138 inherited native runner missing expected anchor")
    s=s.replace(BEFORE,AFTER,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+"""
grep -E '^V138_IOS_REQUEST valid=[01] command=[0-9]{1,10} path_kind=[0-7] mode=[0-9]{1,10}$' "$log" | sort -u
test "$(grep -Ec '^V138_IOS_REQUEST valid=[01] command=[0-9]{1,10} path_kind=[0-7] mode=[0-9]{1,10}$' "$log")" -eq 16
echo 'V138_REQUEST_PROBE verified=1'
""",1)
    return s

if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    with args.output.open("x",encoding="utf-8") as out:
        out.write(derive(args.source.read_text(encoding="utf-8")))
