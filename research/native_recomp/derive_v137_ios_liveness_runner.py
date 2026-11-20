#!/usr/bin/env python3
"""V137 owner original native IOS status probe. Never ticks or changes guest state."""
from pathlib import Path
import argparse
from derive_v136_second_retry_runner import derive as previous
PATTERN=r'^V137_IOS_LIVENESS x1=[01] queued=[0-9]{1,2} event=[01] irq=[01] ee=[01]$'
def derive(source):
    s=previous(source)
    before='python3 "$here/derive_v136_second_retry_harness.py"'
    if s.count(before)!=1:raise ValueError("V137 inherited native harness reference ambiguous")
    s=s.replace(before,'python3 "$here/derive_v137_ios_liveness_harness.py"',1)
    failure="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(failure)!=1:raise ValueError("V137 inherited failure hook missing")
    s=s.replace(failure,"  grep -E '"+PATTERN+"' \"$work/private-native.log\" | sort -u || true\n"+failure,1)
    done="echo 'V136_SECOND_RETRY verified=1'"
    if s.count(done)!=1:raise ValueError("V137 previous native gate missing")
    s=s.replace(done,done+"""
grep -E '^V137_IOS_LIVENESS x1=[01] queued=[0-9]{1,2} event=[01] irq=[01] ee=[01]$' "$log" | sort -u
test "$(grep -Ec '^V137_IOS_LIVENESS x1=[01] queued=[0-9]{1,2} event=[01] irq=[01] ee=[01]$' "$log")" -eq 16
echo 'V137_IOS_PROBE verified=1'
""",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
