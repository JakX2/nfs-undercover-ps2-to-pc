#!/usr/bin/env python3
"""V128 authenticated 71-instruction original helper native execution runner."""
import argparse
from pathlib import Path
from derive_v127_osinit_first_bl_runner import derive as previous

def derive(source):
    s=previous(source)
    changes=(
      ('python3 "$here/derive_v127_osinit_first_bl_harness.py"',
       'python3 "$here/derive_v128_next_function_harness.py"'),
      ('python3 "$here/derive_v127_osinit_first_bl_generator.py"',
       'python3 "$here/derive_v128_next_function_generator.py"'),
      ("V127_TRIAL_PASS","V128_TRIAL_PASS"),
      ("V127_STAGE native_test_passed","V128_STAGE native_test_passed"),
      ("V127_NATIVE_EXIT","V128_NATIVE_EXIT"),
      ("stage=127","stage=128"),
      ("V127 recovered original OSInit first authenticated BL after post-SC GPR save",
       "V128 recovered original 71-instruction OSInit next function and successor"),
    )
    for old,new in changes:
        if old not in s:raise ValueError("V128 runner source anchor missing: "+old)
        s=s.replace(old,new)
    previous_restore="echo 'V127_OSINIT_RESTORE ok=1'"
    if s.count(previous_restore)!=1:
        raise ValueError("V128 inherited authenticated fixture hook unavailable")
    patch='''python3 "$here/restore_v128_next_function.py" "$work/private.dol" "$owner" "$work/helper-v128.dol" \
  > "$work/v128-restore-private.log" 2>&1 || {
  echo 'V128_ORIGINAL_RESTORE ok=0'
  exit 1
}
mv -- "$work/helper-v128.dol" "$work/private.dol"
echo 'V128_ORIGINAL_RESTORE ok=1'
'''
    s=s.replace(previous_restore,previous_restore+"\n"+patch,1)
    old="candidate=\"$(grep -E '^V127_NEXT_CALL pc=[0-9a-f]{8}"
    if s.count(old)!=1:raise ValueError("V128 successor candidate marker ambiguous")
    s=s.replace(old,"candidate=\"$(grep -E '^V128_NEXT_CALL pc=[0-9a-f]{8}",1)
    fail="  echo 'V128_NATIVE_EXIT ok=0'"
    if s.count(fail)!=1:raise ValueError("V128 native failure marker ambiguous")
    s=s.replace(fail,"  grep -E '^V128_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=[01] wire=[01] abi=[01] text=[01]$' \"$work/private-native.log\" | sort -u || true\n"+fail,1)
    marker="echo 'V128_STAGE native_test_passed'"
    if s.count(marker)!=1:raise ValueError("V128 success marker missing")
    s=s.replace(marker,marker+"""
grep -Fx 'V127_NEXT_CALL pc=8052f830 lr=80520970 route=1 wire=1 abi=1 text=1' "$log" | head -n 1
grep -E '^V128_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log" | sort -u
test "$(grep -Ec '^V128_NEXT_CALL pc=[0-9a-f]{8} lr=[0-9a-f]{8} route=1 wire=1 abi=1 text=1$' "$log")" -eq 16 """.rstrip(),1)
    summary="V127_NATIVE_COUNTS"
    if s.count(summary)!=1:raise ValueError("V128 inherited source-private counts ambiguous")
    s=s.replace(summary,"V128_NATIVE_COUNTS",1)
    return s
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:out.write(derive(a.source.read_text(encoding="utf-8")))
