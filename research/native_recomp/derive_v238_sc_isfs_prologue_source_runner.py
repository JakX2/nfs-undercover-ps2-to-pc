#!/usr/bin/env python3
"""V238 genuine ISFS prologue caller and second-mode provenance."""
import argparse
from pathlib import Path
from derive_v237_sc_isfs_reentry_runner import derive as previous
OLD='python3 "$here/derive_v237_sc_isfs_reentry_harness.py"'
NEW='python3 "$here/derive_v238_sc_isfs_prologue_source_harness.py"'
DONE="echo 'V237_SC_ISFS_REENTRY verified=1'"
ENTRY=r'^V238_SAVE seq=[1-8] mapped=[01] nand=[01] logging=[01] other=[01] r11=[01] mode=[01] srcmode=[01] path=[01] sysconf=[01] nandcb=[01]$'
PATTERN=r'^V238_SOURCE saves=[0-8] second=[01] nand=[01] logging=[01] other=[01] r11=[01] modevalid=[01] pathvalid=[01] sysconf=[01] same_ios_mode=[01] ios_invalid=[01]$'
PASS=r'^V238_SOURCE saves=[2-8] second=1 nand=[01] logging=[01] other=[01] r11=[01] modevalid=[01] pathvalid=[01] sysconf=[01] same_ios_mode=[01] ios_invalid=1$'
def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V238 inherited owner original V237 runner changed")
    s=s.replace(OLD,NEW,1)
    fail="  echo 'V130_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:
        raise ValueError("V238 native owner failure exit changed")
    for pattern in (ENTRY,PATTERN):
        s=s.replace(fail,'  grep -E "'+pattern+'" "$work/private-native.log" | sort -u || true\n'+fail,1)
    compile_line='python3 "$here/classify_v77_compile_failure.py" "$work/native-compile.log" "$unit"'
    if s.count(compile_line)!=1:
        raise ValueError("V238 native compiler failure hook changed")
    s=s.replace(compile_line,
        'python3 "$V110_SOURCE_ROOT/diagnose_v238_compile_failure.py" "$work/native-compile.log" "$work/harness.cpp" || true\n      '+
        compile_line,1)
    return s.replace(DONE,DONE+f"""
grep -E '{ENTRY}' "$log" | sort -u
grep -E '{PATTERN}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
echo 'V238_SC_ISFS_PROLOGUE verified=1'
""",1)
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
