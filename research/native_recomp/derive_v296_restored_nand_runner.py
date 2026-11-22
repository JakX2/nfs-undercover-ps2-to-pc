#!/usr/bin/env python3
"""V296: privately rebuild the V295 candidate with read-only service probes."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
LINK='if g++ "$work/v250-harness.o" "$work/v294-generated.o" "$work/loader.o" \\'
DONE="echo 'V295_BOUNDED_CANDIDATE inspected=1'"
COMPILE=r'''
# An observational native harness only. It does not change the restored
# guest code, hardware state, callback results or IPC/NAND replies.
python3 "$V110_SOURCE_ROOT/derive_v296_service_harness.py"   "$work/v250-harness.cpp" "$work/v296-harness.cpp"
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label        -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include"        -c "$work/v296-harness.cpp" -o "$work/v296-harness.o"        > "$work/v296-compile.log" 2>&1; then
  echo 'V296_HARNESS_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py"     "$work/v296-compile.log" harness || true
  echo 'V296_HARNESS_STAGE compile=0'
  exit 1
fi
'''
AUDIT=r'''
python3 "$V110_SOURCE_ROOT/analyze_v296_native_frontier.py"    "$work/v295-native.log" "$work/v296-harness.cpp" "$v295_rc"
echo 'V296_SERVICE_PROBE inspected=1'
'''

def patch(source: str) -> str:
    if source.count(LINK)!=1 or source.count(DONE)!=1:
        raise ValueError("V296 verified V295 native runner seam changed")
    return (source.replace(LINK, COMPILE + '\n' +
                           LINK.replace("v250-harness.o","v296-harness.o"), 1)
                  .replace(DONE, DONE + "\n" + AUDIT, 1))

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v296-") as td:
        previous = Path(td)/"v295.sh"
        result = subprocess.run(
            [sys.executable,str(HERE/"derive_v295_restored_nand_runner.py"),
             str(args.source),str(previous)],
            capture_output=True,text=True)
        if result.returncode:
            raise ValueError("V296 predecessor derivation failed")
        with args.output.open("x",encoding="utf-8") as out:
            out.write(patch(previous.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
