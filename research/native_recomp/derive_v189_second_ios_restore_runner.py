#!/usr/bin/env python3
"""V189 original Wii OS restore-interrupt helper after second IOS Y2 ACK."""
import argparse
from pathlib import Path
from derive_v188_second_ios_osdi_runner import derive as previous

OLD='python3 "$here/derive_v188_second_ios_osdi_harness.py"'
NEW='python3 "$here/derive_v189_second_ios_restore_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V188_SC_OSDI verified=1'"
PATTERN=r'^V189_SC_NEXT y2=[01] flag=[01] queue=[01] request=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] sc=[01] ee=[01] ready=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V189_SC_NEXT y2=[01] flag=[01] queue=1 request=1 guest=1 caller=1 coherent=1 mapped=1 sc=1 ee=[01] ready=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
STATE=r'^V189_SC_STATE guest=[01] queue=[01] irq=[01] sc=[01] ee=[01] ready=[01]$'
PASS_STATE=r'^V189_SC_STATE guest=1 queue=1 irq=1 sc=1 ee=[01] ready=[01]$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V189 inherited original owner runner anchors differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+STATE+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    # The previous OSDI check remains strict at the real V188 entry, but
    # restoring MSR.EE can legitimately change its final observed state.
    old="grep -Fx 'V188_SC_STATE guest=1 queue=1 irq=1 masked=1 sc=1' \"$log\" | sort -u"
    new="grep -E '^V188_SC_STATE guest=1 queue=1 irq=1 masked=[01] sc=1$' \"$log\" | sort -u"
    if s.count(old)!=1:
        raise ValueError("V189 inherited final OSDI state diagnostic changed")
    s=s.replace(old,new,1)
    old_count="test \"$(grep -Ec '^V188_SC_STATE guest=1 queue=1 irq=1 masked=1 sc=1$' \"$log\")\" -eq 16"
    new_count="test \"$(grep -Ec '^V188_SC_STATE guest=1 queue=1 irq=1 masked=[01] sc=1$' \"$log\")\" -eq 16"
    if s.count(old_count)!=1:
        raise ValueError("V189 original V188 terminal count differs")
    s=s.replace(old_count,new_count,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -E '{PASS_STATE}' "$log" | sort -u
test "$(grep -Ec '{PASS_STATE}' "$log")" -eq 16
echo 'V189_SC_RESTORE verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
