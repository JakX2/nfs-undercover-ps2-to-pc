#!/usr/bin/env python3
"""V293: retain V292 authenticated run, validate private reversible restoration."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile
HERE=Path(__file__).resolve().parent
DONE="echo 'V292_AOT_REACH verified=1'"
EXTRA='''
if python3 "$V110_SOURCE_ROOT/restore_v293_private_nand.py" \
  "$owner" "$work/v293-original.elf" "$work/private-v248.dol" \
  "$work/private-v293.dol" > "$work/v293-restore.log" 2>&1; then
  grep -Fx 'V293_RESTORE_AUDIT verified=1' "$work/v293-restore.log"
  grep -E '^V293_NAND_RESTORE owner=1 funcs=4 changed=[0-9]{1,5} total_words=[0-9]{1,5} roundtrip=1 candidate=1$' "$work/v293-restore.log"
  test "$(grep -Ec '^V293_RESTORED pc=[0-9a-f]{8} words=[0-9]{1,4} already=[0-9]{1,4} nop=[0-9]{1,4} foreign=0$' "$work/v293-restore.log")" -eq 4
  grep -E '^V293_RESTORED pc=[0-9a-f]{8} words=[0-9]{1,4} already=[0-9]{1,4} nop=[0-9]{1,4} foreign=0$' "$work/v293-restore.log"
else
  grep -Fx 'V293_RESTORE_AUDIT verified=0' "$work/v293-restore.log" || true
  echo 'V293_RESTORE result=failed'
  exit 1
fi
test -s "$work/private-v293.dol"
echo 'V293_PRIVATE_RESTORE verified=1'
'''
# Need a private owner ELF inside inherited mktemp, not within public sources.
PRE="echo 'V292_AOT_REACH verified=1'"
ELF_COPY='''# V293 owner-private ELF is supplied only via the owner runner environment.
test -s "$V293_PRIVATE_ELF"
cp -- "$V293_PRIVATE_ELF" "$work/v293-original.elf"
chmod 600 "$work/v293-original.elf"
'''
def patch(source):
    if source.count(DONE)!=1:raise ValueError("V292 owner-native runner seam changed")
    return source.replace(DONE,DONE+"\n"+ELF_COPY+EXTRA,1)
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v293-run-") as td:
        prev=Path(td)/"v292.sh"
        r=subprocess.run(
            [sys.executable,str(HERE/"derive_v292_nand_aot_reach_runner.py"),
             str(a.source),str(prev)],
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if r.returncode:raise ValueError("V293 predecessor derivation failed")
        with a.output.open("x",encoding="utf-8") as stream:
            stream.write(patch(prev.read_text(encoding="utf-8")))
    return 0
if __name__=="__main__":
    sys.exit(main())
