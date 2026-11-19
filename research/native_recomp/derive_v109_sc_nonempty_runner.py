#!/usr/bin/env python3
"""Derive a strict V109 owner-local native execution runner from V108.

The V104 success gate observes an alternate empty-fixture async-open
route. V109's authenticated nonempty pathname path needs its own
independent terminal and assertion checks after the same native build.
"""
from derive_v108_sc_literal_runner import derive as previous

def derive(source):
    s=previous(source)
    old="derive_v108_sc_literal_restore_harness.py"
    if s.count(old)!=1:
        raise ValueError("V109 original harness hook differs")
    s=s.replace(old,"derive_v109_sc_nonempty_harness.py",1)
    if s.count("V104_SOURCE_ROOT")!=1:
        raise ValueError("V109 source root relay absent")
    s=s.replace("V104_SOURCE_ROOT","V109_SOURCE_ROOT",1)
    compiled="echo 'V104_STAGE native_compiled'"
    old_success="echo 'V104_STAGE native_test_passed'"
    native='"$work/native" "$work/private.dol" owner "$owner"'
    if s.count(compiled)!=1 or s.count(old_success)!=1 or s.count(native)!=1:
        raise ValueError("V109 authenticated native build/execution boundary differs")
    if not (s.index(compiled)<s.index(native)<s.index(old_success)):
        raise ValueError("V109 native execution order differs")
    # Keep the complete verified owner fixture, generator, compiler and
    # native binary link unchanged. Replace only the V104-specific
    # execution/gating trailer, with no private log publication.
    result=s[:s.index(compiled)+len(compiled)]+r"""
if "$work/native" "$work/private.dol" owner "$owner" > "$work/private-native.log" 2>&1; then
  echo 'V109_NATIVE_EXIT ok=1'
else
  python3 "$here/classify_v67_native_failure.py" "$work/private-native.log" "$work/harness.cpp" || true
  grep -E '^V109_SC_SECOND_SOURCE order=[01] mapped=[01] terminated=[01] empty=[01] output=[01] abi=[01]$|^V109_SC_SECOND_COPY input=[01] bounded=[01]$|^V109_SC_NEXT_LENGTH route=[01] data=[01] prior=[01]$' "$work/private-native.log" | sort -u || true
  echo 'V109_NATIVE_EXIT ok=0'
  exit 1
fi
log="$work/private-native.log"
for trial in $(seq 1 16); do
  grep -Fxq "V109_TRIAL_PASS trial=$trial" "$log"
done
test "$(grep -Ec '^V109_TRIAL_PASS trial=[0-9]{1,2}$' "$log")" -eq 16
grep -Fxq 'V108_SC_RESTORE owner=1 empty_before=1 exact=1' "$log"
grep -Fxq 'V109_SC_SECOND_COPY input=1 bounded=1' "$log"
grep -Fxq 'V109_SC_NEXT_LENGTH route=1 data=1 prior=1' "$log"
grep -Eq '^PASS: [0-9]+ V109 recovered continuous original __start->nonempty SC second string copy assertions; mode=owner trials=16 stop=0x80544ac0$' "$log"
echo 'V109_STAGE native_test_passed'
grep -E '^V109_SC_SECOND_SOURCE order=[01] mapped=[01] terminated=[01] empty=[01] output=[01] abi=[01]$|^V109_SC_SECOND_COPY input=[01] bounded=[01]$|^V109_SC_NEXT_LENGTH route=[01] data=[01] prior=[01]$' "$log" | sort -u
echo 'PASS: original Wii nonempty SC path executed authentic second string copy'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80544AC0 stage=109'
"""
    return result

def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    args=parser.parse_args()
    result=derive(args.source.read_text(encoding="utf-8"))
    with args.output.open("x",encoding="utf-8") as out:out.write(result)

if __name__=="__main__":main()
