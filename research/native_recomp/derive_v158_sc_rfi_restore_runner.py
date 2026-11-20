#!/usr/bin/env python3
"""V158 sixteen owner-original SC context-load/RFI proof trials."""
import argparse
from pathlib import Path
from derive_v157_sc_rescheduler_next_runner import derive as previous

OLD='python3 "$here/derive_v157_sc_rescheduler_next_harness.py"'
NEW='python3 "$here/derive_v158_sc_rfi_restore_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V157_SC_RESCHED_NEXT verified=1'"
PATTERN=r'^V158_SC_RFI pc=[01] msr=[01] regs=[01] waiting=[01] running=[01] ready_thread=[01] linked=[01] lifecycle=[01] irq=[01] reply=[01] coherent=[01] ee=[01] ready=[01] old_pc=[01]$'
PASS=r'^V158_SC_RFI pc=1 msr=1 regs=1 waiting=0 running=1 ready_thread=0 linked=[01] lifecycle=1 irq=1 reply=1 coherent=1 ee=1 ready=1 old_pc=[01]$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V158 owner-original native runner predecessor gates differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -Fx "V158_SC_LOAD_ENTRY route=1" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "^V158_SC_LOAD_ARG route=[01] masked=[01] aligned=[01] mapped=[01] idle=[01] thread=[01]$" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -Fx 'V158_SC_LOAD_ENTRY route=1' "$log" | sort -u
test "$(grep -Fxc 'V158_SC_LOAD_ENTRY route=1' "$log")" -eq 16
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V158_SC_RFI verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
