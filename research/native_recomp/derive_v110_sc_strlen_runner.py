#!/usr/bin/env python3
"""V110 native runner follows original SC strlen into selected child."""
from derive_v109_sc_nonempty_runner import derive as previous
def derive(source):
    s=previous(source)
    for old,new in (("derive_v109_sc_nonempty_harness.py","derive_v110_sc_strlen_harness.py"),
                    ("V109_SOURCE_ROOT","V110_SOURCE_ROOT")):
        if s.count(old)!=1:raise ValueError("V110 runner anchor missing or ambiguous: "+old)
        s=s.replace(old,new,1)
    compiled="echo 'V104_STAGE native_compiled'"
    if s.count(compiled)!=1:raise ValueError("V110 compiled checkpoint absent")
    s=s[:s.index(compiled)+len(compiled)]+r"""
if "$work/native" "$work/private.dol" owner "$owner" > "$work/private-native.log" 2>&1; then
  echo 'V110_NATIVE_EXIT ok=1'
else
  python3 "$here/classify_v67_native_failure.py" "$work/private-native.log" "$work/harness.cpp" || true
  grep -E '^V110_ASSERT_HOOK pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V110_TRIAL_START trial=[0-9]{1,2}$|^V110_TRIAL_PASS trial=[0-9]{1,2}$|^V109_SC_SECOND_COPY input=[01] bounded=[01]$|^V110_SC_STRLEN input=[01] bounded=[01] empty=[01]$|^V110_SC_CONTINUE route=[01] data=[01] abi=[01] prior=[01] branch=[123]$' "$work/private-native.log" | sort -u || true
  echo 'V110_NATIVE_EXIT ok=0'
  exit 1
fi
log="$work/private-native.log"
for trial in $(seq 1 16); do
  grep -Fxq "V110_TRIAL_PASS trial=$trial" "$log"
done
test "$(grep -Ec '^V110_TRIAL_PASS trial=[0-9]{1,2}$' "$log")" -eq 16
grep -Fxq 'V108_SC_RESTORE owner=1 empty_before=1 exact=1' "$log"
grep -Fxq 'V109_SC_SECOND_COPY input=1 bounded=1' "$log"
grep -Eq '^V110_SC_STRLEN input=1 bounded=1 empty=[01]$' "$log"
grep -Eq '^V110_SC_CONTINUE route=1 data=1 abi=1 prior=1 branch=[123]$' "$log"
grep -Eq '^PASS: [0-9]+ V110 recovered continuous original __start->nonempty SC strlen continuation assertions; mode=owner trials=16 stop=0x(8051e518|804f1e2c|8051e3dc)$' "$log"
echo 'V110_STAGE native_test_passed'
grep -E '^V109_SC_SECOND_COPY input=[01] bounded=[01]$|^V110_SC_STRLEN input=[01] bounded=[01] empty=[01]$|^V110_SC_CONTINUE route=[01] data=[01] abi=[01] prior=[01] branch=[123]$' "$log" | sort -u
branch="$(grep -E '^V110_SC_CONTINUE route=1 data=1 abi=1 prior=1 branch=[123]$' "$log" | tail -n 1 | sed -E 's/.*branch=([123])$/\1/')"
case "$branch" in
  1) target=0x8051E518;;
  2) target=0x804F1E2C;;
  3) target=0x8051E3DC;;
  *) echo 'V110 original SC continuation branch unavailable' >&2; exit 1;;
esac
echo 'PASS: original SC strlen returned to authentic continuation'
echo "BOOT_PROGRESS entry=0x8000403C pc=$target stage=110"
"""
    return s
def main():
    import argparse
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:f.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
