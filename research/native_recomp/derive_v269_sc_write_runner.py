#!/usr/bin/env python3
"""V269 original Wii native runner: V263 guest trace + guest SC write watch."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
OLD='python3 "$V110_SOURCE_ROOT/derive_v262_ipc_state_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v269_sc_write_harness.py"'
DONE="echo 'V263_HOTSPOT verified=1'"
MORE='''
python3 "$V110_SOURCE_ROOT/analyze_v269_sc_write.py" "$work/v250-native.log"
echo 'V269_SC_WATCH verified=1'
'''

def patch(text:str)->str:
    if text.count(OLD)!=1 or text.count(DONE)!=1:
        raise ValueError("V269 V263 runner source seam changed")
    return text.replace(OLD,NEW,1).replace(DONE,DONE+MORE,1)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v269-native-") as td:
        child=Path(td)/"v263.sh"
        proc=subprocess.run(
            [sys.executable,str(HERE/"derive_v263_hotspot_runner.py"),
             str(a.source),str(child)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if proc.returncode:
            raise ValueError("V269 V263 native runner derivation failed")
        with a.output.open("x",encoding="utf-8") as out:
            out.write(patch(child.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
