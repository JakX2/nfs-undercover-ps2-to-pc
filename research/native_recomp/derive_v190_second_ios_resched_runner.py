#!/usr/bin/env python3
"""V190 native guest rescheduler successor after second IOS Y2 ACK."""
import argparse
from pathlib import Path
from derive_v189_second_ios_restore_runner import derive as previous

OLD='python3 "$here/derive_v189_second_ios_restore_harness.py"'
NEW='python3 "$here/derive_v190_second_ios_resched_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V189_SC_RESTORE verified=1'"
PATTERN=r'^V190_SC_NEXT y2=[01] flag=[01] queue=[01] request=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] sc=[01] ee=[01] ready=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V190_SC_NEXT y2=[01] flag=[01] queue=1 request=1 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=[01] ready=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
STATE=r'^V190_SC_STATE guest=[01] queue=[01] irq=[01] sc=[01]$'
CLEANUP=r'^V190_V95_CLEANUP phase=[01] ack=[01] target=[01] seen=[01] free=[01] resume=[01] reply=[01]$'
DUP=r'^V190_V95_DUP phase=[01] auth=[01] target=[01] call=[01] first=[01]$'
PASS_STATE=r'^V190_SC_STATE guest=1 queue=1 irq=1 sc=1$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V190 owner runner inherited original-free anchors changed")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+DUP+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+CLEANUP+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    # The V38 numeric code is indexed in the actual generated harness.
    # Do not decode it using a separate derived-source catalog.
    old_classifier='python3 "$here/classify_v67_native_failure.py"'
    if s.count(old_classifier)!=1:
        raise ValueError("V190 owner-native classifier injection point differs")
    s=s.replace(old_classifier,
        'python3 "$here/diagnose_v190_native_guard.py" "$work/private-native.log" "$work/harness.cpp"\\n  '+old_classifier,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -Fx 'V190_SC_STATE guest=1 queue=1 irq=1 sc=1' "$log" | sort -u
test "$(grep -Ec '{PASS_STATE}' "$log")" -eq 16
echo 'V190_SC_RESCHED verified=1'
""",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
