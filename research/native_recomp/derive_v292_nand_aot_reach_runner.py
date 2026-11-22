#!/usr/bin/env python3
"""V292 inherit V289 owner-native generator, inspect its private AOT mapping."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent
DONE="echo 'V289_NAND_ENTRY verified=1'"
EXTRA='''
python3 "$V110_SOURCE_ROOT/audit_v292_nand_aot_reach.py" \
  "$owner" "$work/private-v248.dol" "$work/generated-v248/output.cpp"
echo 'V292_AOT_REACH verified=1'
'''
def patch(source):
    if source.count(DONE)!=1:raise ValueError("V289 runner checksum seam changed")
    return source.replace(DONE,DONE+EXTRA,1)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v292-run-") as td:
        prev=Path(td)/"v289.sh"
        r=subprocess.run([sys.executable,
            str(HERE/"derive_v289_nand_entry_r3_runner.py"),
            str(a.source),str(prev)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if r.returncode:raise ValueError("V292 inherited V289 runner failed")
        with a.output.open("x",encoding="utf-8") as out:
            out.write(patch(prev.read_text(encoding="utf-8")))
    return 0
if __name__=="__main__":
    sys.exit(main())
