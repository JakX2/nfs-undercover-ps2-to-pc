#!/usr/bin/env python3
"""V278: reuse authenticated V269 owner native runner, add entry census."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
OLD='python3 "$V110_SOURCE_ROOT/derive_v269_sc_write_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v278_fca4_entry_harness.py"'
DONE="echo 'V269_SC_WATCH verified=1'"
EXTRA='''
python3 "$V110_SOURCE_ROOT/analyze_v278_fca4_entry.py" "$work/v250-native.log"
echo 'V278_FCA4_ENTRY verified=1'
'''

def patch(source:str)->str:
    if source.count(OLD)!=1 or source.count(DONE)!=1:
        raise ValueError("V278 inherited V269 owner-native runner changed")
    return source.replace(OLD,NEW,1).replace(DONE,DONE+EXTRA,1)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v278-run-") as td:
        intermediate=Path(td)/"v269.sh"
        result=subprocess.run(
            [sys.executable,str(HERE/"derive_v269_sc_write_runner.py"),
             str(a.source),str(intermediate)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if result.returncode:
            raise ValueError("V278 inherited V269 runner generation failed")
        with a.output.open("x",encoding="utf-8") as out:
            out.write(patch(intermediate.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
