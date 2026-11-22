#!/usr/bin/env python3
"""V285 original-native runner: keep V278 checks and add r3 producer entry."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
OLD='python3 "$V110_SOURCE_ROOT/derive_v278_fca4_entry_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v285_nand_early_service_harness.py"'
DONE="echo 'V278_FCA4_ENTRY verified=1'"
EXTRA='''
python3 "$V110_SOURCE_ROOT/analyze_v285_nand_early_service.py" "$work/v250-native.log"
echo 'V285_NAND_SERVICE verified=1'
'''

def patch(source:str)->str:
    if source.count(OLD)!=1 or source.count(DONE)!=1:
        raise ValueError("V285 authentic V278 runner source seam changed")
    return source.replace(OLD,NEW,1).replace(DONE,DONE+EXTRA,1)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v285-run-") as td:
        prev=Path(td)/"v278.sh"
        proc=subprocess.run(
            [sys.executable,str(HERE/"derive_v278_fca4_entry_runner.py"),
             str(a.source),str(prev)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if proc.returncode:
            raise ValueError("V285 inherited V278 native runner derivation failed")
        with a.output.open("x",encoding="utf-8") as out:
            out.write(patch(prev.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
