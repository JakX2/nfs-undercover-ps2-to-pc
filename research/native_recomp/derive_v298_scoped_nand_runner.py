#!/usr/bin/env python3
"""V298: run bounded owner-native NAND with only stale V178 observer scoped."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
LINK='if g++ "$work/v296-harness.o" "$work/v294-generated.o" "$work/loader.o" \\'
DONE="echo 'V296_SERVICE_PROBE inspected=1'"
PRE=r'''
python3 "$V110_SOURCE_ROOT/derive_v298_scope_reply_observer.py"    "$work/v296-harness.cpp" "$work/v298-harness.cpp"
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label        -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include"        -c "$work/v298-harness.cpp" -o "$work/v298-harness.o"        > "$work/v298-compile.log" 2>&1; then
  echo 'V298_HARNESS_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py"     "$work/v298-compile.log" harness || true
  echo 'V298_HARNESS_STAGE compile=0'
  exit 1
fi
'''
AFTER=r'''
python3 "$V110_SOURCE_ROOT/analyze_v298_scope_native.py"    "$work/v295-native.log" "$work/v298-harness.cpp" "$v295_rc"
echo 'V298_RETIRED_OBSERVER inspected=1'
'''

def patch(source: str) -> str:
    if source.count(LINK)!=1 or source.count(DONE)!=1:
        raise ValueError("V298 owner-native compiler seam changed")
    return (source.replace(LINK,PRE+"\n"+
                           LINK.replace("v296-harness.o","v298-harness.o"),1)
                  .replace(DONE,DONE+"\n"+AFTER,1))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v298-") as td:
        prev=Path(td)/"v296.sh"
        r=subprocess.run(
            [sys.executable,str(HERE/"derive_v296_restored_nand_runner.py"),
             str(a.source),str(prev)],capture_output=True,text=True)
        if r.returncode:
            raise ValueError("V298 inherited owner-native runner changed")
        with a.output.open("x",encoding="utf-8") as dst:
            dst.write(patch(prev.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
