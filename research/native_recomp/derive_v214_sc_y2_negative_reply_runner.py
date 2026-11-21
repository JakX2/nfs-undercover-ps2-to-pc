#!/usr/bin/env python3
"""V214 faithful negative second IOS_Open response at authentic native yield."""
import argparse
from pathlib import Path
from derive_v207_sc_y2_helper_next_runner import derive as previous

OLD='python3 "$here/derive_v207_sc_y2_helper_next_harness.py"'
NEW='python3 "$here/derive_v214_sc_y2_negative_reply_harness.py"'
DONE="echo 'V207_SC_Y2_HELPER_NEXT verified=1'"
PATTERN=r'^V214_Y2_NEGATIVE invalid=[01] mode=[01] path=[01] published=[01] irq=[01] drained=[01] cpu=[01] sc=[01]$'
PASS=r'^V214_Y2_NEGATIVE invalid=1 mode=1 path=1 published=1 irq=1 drained=1 cpu=1 sc=1$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V214 inherited owner-original V207 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V214 native owner failure-exit changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    s=s.replace(fail,'  python3 "$V110_SOURCE_ROOT/diagnose_v214_native_failure.py" "$work/private-native.log" "$work/harness.cpp" || true\n'+fail,1)
    compile_line='python3 "$here/classify_v77_compile_failure.py" "$work/native-compile.log" "$unit"'
    if s.count(compile_line)!=1:
        raise ValueError("V214 expected compile error guard changed")
    s=s.replace(compile_line,
        'python3 "$V110_SOURCE_ROOT/diagnose_v214_compile_failure.py" "$work/native-compile.log" "$unit" || true\\n      '+
        compile_line,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V214_SC_Y2_NEGATIVE verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
