#!/usr/bin/env python3
"""Derive V109 original nonempty SC branch runner from V108 fixture."""
from derive_v108_sc_literal_runner import derive as previous

def derive(source):
    s=previous(source)
    old="derive_v108_sc_literal_restore_harness.py"
    if s.count(old)!=1:raise ValueError("V109 original harness hook differs")
    s=s.replace(old,"derive_v109_sc_nonempty_harness.py",1)
    if s.count("V104_SOURCE_ROOT")!=1:
        raise ValueError("V109 source root relay absent")
    s=s.replace("V104_SOURCE_ROOT","V109_SOURCE_ROOT",1)
    start="echo 'V104_STAGE native_test_passed'"
    if s.count(start)!=1 or not s.rstrip().endswith(
        "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104'"):
        raise ValueError("V109 unexpected verified V104 trailer")
    success="""echo 'V109_STAGE native_test_passed'
log="$work/private-native.log"
for trial in $(seq 1 16); do
  grep -Fxq "V109_TRIAL_PASS trial=$trial" "$log"
done
test "$(grep -Ec '^V109_TRIAL_PASS trial=[0-9]{1,2}$' "$log")" -eq 16
grep -Fx 'V108_SC_RESTORE owner=1 empty_before=1 exact=1' "$log"
grep -Fx 'V109_SC_SECOND_COPY input=1 bounded=1' "$log"
grep -Fx 'V109_SC_NEXT_LENGTH route=1 data=1 prior=1' "$log"
grep -Eq '^PASS: [0-9]+ V109 recovered continuous original __start->nonempty SC second string copy assertions; mode=owner trials=16 stop=0x80544ac0$' "$log"
echo 'PASS: original Wii nonempty SC path executed second authentic string copy'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80544AC0 stage=109'
"""
    return s[:s.index(start)]+success
