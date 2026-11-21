#!/usr/bin/env python3
"""V215 authentic second IOS negative reply Y1 external interrupt entry."""
import argparse
from pathlib import Path
from derive_v212_sc_y2_rfi_runner import derive as previous

OLD='python3 "$here/derive_v212_sc_y2_rfi_harness.py"'
NEW='python3 "$here/derive_v215_sc_y1_negative_vector_harness.py"'
DONE="echo 'V212_SC_Y2_RFI verified=1'"
PATTERN=r'^V215_Y1_VECTOR pump=[01] published=[01] signal=[01] empty=[01] cpu=[01] entered=[01] saved=[01] regs=[01] masked=[01] sc=[01]$'
PASS=r'^V215_Y1_VECTOR pump=1 published=1 signal=1 empty=1 cpu=1 entered=1 saved=1 regs=1 masked=1 sc=1$'

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V215 inherited V212 native owner runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V215 original native failure anchor changed")
    s=s.replace(fail,'  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    compile_line='python3 "$here/classify_v77_compile_failure.py" "$work/native-compile.log" "$unit"'
    if s.count(compile_line)!=1:
        raise ValueError("V215 public harness compiler guard changed")
    s=s.replace(compile_line,
        'python3 "$V110_SOURCE_ROOT/diagnose_v215_compile_failure.py" "$work/native-compile.log" "$work/harness.cpp" "$unit" || true\\n      '+
        compile_line,1)
    return s.replace(DONE,DONE+f"""
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V215_SC_Y1_NEGATIVE_VECTOR verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as f:
        f.write(derive(args.source.read_text(encoding="utf-8")))
