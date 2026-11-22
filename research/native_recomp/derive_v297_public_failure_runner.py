#!/usr/bin/env python3
"""V297: inherit bounded V296 original-native run and locate public failure."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
DONE="echo 'V296_SERVICE_PROBE inspected=1'"
EXTRA=r'''
python3 "$V110_SOURCE_ROOT/analyze_v297_public_failure.py"     "$work/v295-native.log" "$work/v296-harness.cpp" "$v295_rc"
echo 'V297_ASSERTION_PROVENANCE inspected=1'
'''

def patch(source: str) -> str:
    if source.count(DONE)!=1 or "analyze_v296_native_frontier.py" not in source:
        raise ValueError("V297 V296 owner-native seam changed")
    return source.replace(DONE,DONE+"\n"+EXTRA,1)

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    opts=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v297-") as td:
        previous=Path(td)/"v296.sh"
        result=subprocess.run(
            [sys.executable,str(HERE/"derive_v296_restored_nand_runner.py"),
             str(opts.source),str(previous)],
            capture_output=True,text=True)
        if result.returncode:
            raise ValueError("V297 predecessor derivation failed")
        with opts.output.open("x",encoding="utf-8") as out:
            out.write(patch(previous.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
