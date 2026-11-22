#!/usr/bin/env python3
"""V295: privately execute V294's compiled original NAND AOT under a hard limit."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
DONE = "echo 'V294_RESTORED_AOT verified=1'"
EXTRA = r'''
# V295 only: launch the separate restored executable with authentic Wii
# guest state and callbacks. Never substitute IOS/NAND/SYSCONF values.
# No raw game output or generated code is published.
ulimit -c 0
set +e
timeout --signal=TERM --kill-after=3s 30s     "$work/v294-native" "$work/private-v293.dol" owner-callback "$owner"     > "$work/v295-native.log" 2>&1
v295_rc=$?
set -e
if python3 "$V110_SOURCE_ROOT/analyze_v295_restored_native.py"     "$work/v295-native.log" "$v295_rc"; then
  echo 'V295_BOUNDED_CANDIDATE inspected=1'
else
  echo 'V295_BOUNDED_CANDIDATE inspected=0'
  exit 1
fi
'''

def patch(source: str) -> str:
    if source.count(DONE) != 1 or "V294_AOT_STAGE link=1" not in source:
        raise ValueError("V294 private native runner seam changed")
    return source.replace(DONE, DONE + "\n" + EXTRA, 1)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="v295-") as td:
        previous = Path(td) / "v294.sh"
        run = subprocess.run(
            [sys.executable, str(HERE / "derive_v294_restored_nand_aot_runner.py"),
             str(args.source), str(previous)],
            text=True, capture_output=True)
        if run.returncode:
            raise ValueError("V295 predecessor derivation failed")
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(patch(previous.read_text(encoding="utf-8")))
    return 0

if __name__ == "__main__":
    sys.exit(main())
