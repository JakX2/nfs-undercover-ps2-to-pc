#!/usr/bin/env python3
"""V131 original Wii retry-state probe reusing verified V130 native stop."""
import argparse
from pathlib import Path
from derive_v130_irq_restore_runner import derive as previous

PATTERN=r'^V131_RETRY_STATE pc=[0-9a-f]{8} lr=[0-9a-f]{8} r3=[0-9]{1,10} eq=[01] back=[01]$'
def derive(source):
    s=previous(source)
    old='python3 "$here/derive_v130_irq_restore_harness.py"'
    if s.count(old)!=1:raise ValueError("V131 harness selector unavailable")
    s=s.replace(old,'python3 "$here/derive_v131_retry_state_harness.py"',1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    trace='  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
    if s.count(fail)!=1:raise ValueError("V131 inherited native failure gate differs")
    s=s.replace(fail,trace+fail,1)
    done="echo 'V130_STAGE native_test_passed'"
    if s.count(done)!=1:raise ValueError("V131 inherited test gate differs")
    additional="""
grep -E '^V131_RETRY_STATE pc=8052f830 lr=80520970 r3=[0-9]{1,10} eq=1 back=1$' "$log" | sort -u
test "$(grep -Ec '^V131_RETRY_STATE pc=8052f830 lr=80520970 r3=[0-9]{1,10} eq=1 back=1$' "$log")" -eq 16
echo 'V131_STATE_PROBE verified=1'
"""
    s=s.replace(done,done+additional,1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
