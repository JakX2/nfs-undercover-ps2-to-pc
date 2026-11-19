#!/usr/bin/env python3
"""Derive V104 runner from V103."""
import argparse
from pathlib import Path
from derive_v103_sc_async_entry_runner import derive as previous

EDITS = [
  [
    "V103_SOURCE_ROOT",
    "V104_SOURCE_ROOT"
  ],
  [
    "run_v103_continuous_sc_async_entry.sh",
    "run_v104_continuous_sc_async_submit.sh"
  ],
  [
    "derive_v103_sc_async_entry_harness.py",
    "derive_v104_sc_async_submit_harness.py"
  ],
  [
    "derive_v103_sc_async_entry_generator.py",
    "derive_v104_sc_async_submit_generator.py"
  ],
  [
    "echo 'V103_STAGE geometry_verified'",
    "python3 \"$here/restore_sc_async_submit_v104.py\" \"$work/private.dol\" \"$owner\" \"$work/sc-async-submit.dol\" > \"$work/extend-sc-async-submit.log\" 2>&1 || {\n    echo 'V104 original IOS_OpenAsync body extension failed; details withheld' >&2; exit 1;\n  }\nmv -- \"$work/sc-async-submit.dol\" \"$work/private.dol\"\necho 'V103_STAGE geometry_verified'"
  ],
  [
    "V103 recovered continuous original __start->IOS_OpenAsync entry assertions; mode=owner trials=16 stop=0x8051982c",
    "V104 recovered continuous original __start->IOS_OpenAsync request submit assertions; mode=owner trials=16 stop=0x805195ec"
  ],
  [
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x8051982C stage=103'",
    "echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104'"
  ],
  [
    "PASS: original Wii continuous __start executed SC asynchronous wrapper into IOS_OpenAsync",
    "PASS: original Wii continuous __start constructed authentic IOS_OpenAsync request"
  ],
  [
    "  echo 'V103 original SC async open entry failed; details withheld' >&2",
    "  grep -E '^V104_ASYNC_SAVE route=[01]$|^V104_ASYNC_CACHE bounded=[01]$|^V104_ASYNC_SUBMIT route=[01] request=[01] mode=[01] path=[01] abi=[01] prior=[01]$|^V104_ASYNC_SYSCALL order=[01] lines=[01]$|^V104_FAIL_HOOK pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_FALLTHROUGH pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} phase=[0-9]{1,2} cache=[0-9]{1,2}$|^V104_DEPENDENCY pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_TRACE seq=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$' \"$work/private-native.log\" | sort -u || true\n  echo 'V104 original IOS_OpenAsync request submit failed; details withheld' >&2"
  ],
  [
    "echo 'V103_STAGE native_test_passed'",
    "echo 'V104_STAGE native_test_passed'\ngrep -E '^V104_ASYNC_SAVE route=[01]$|^V104_ASYNC_CACHE bounded=[01]$|^V104_ASYNC_SUBMIT route=[01] request=[01] mode=[01] path=[01] abi=[01] prior=[01]$|^V104_ASYNC_SYSCALL order=[01] lines=[01]$|^V104_FAIL_HOOK pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_FALLTHROUGH pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8} phase=[0-9]{1,2} cache=[0-9]{1,2}$|^V104_DEPENDENCY pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$|^V104_TRACE seq=[0-9]{1,2} pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$' \"$work/private-native.log\" | sort -u"
  ]
]

def derive(source):
    source = previous(source)
    for old, new in EDITS:
        if source.count(old) != 1:
            raise ValueError("V83 source anchor missing or ambiguous")
        source = source.replace(old, new, 1)
    out=source.replace("V103_STAGE", "V104_STAGE").replace("V103_TRIAL_PASS", "V104_TRIAL_PASS")
    anchor="echo 'V104_STAGE native_test_passed'"
    if out.count(anchor)!=1:raise ValueError("V104 native success anchor missing")
    # Keep successful game-code execution distinct from informational grep
    # filters. Verify the complete 16-trial checkpoint and critical
    # predicates before advertising the original async submit boundary.
    # No private fixture text, paths, game code, or arbitrary log lines
    # are printed by the owner runner.
    success="""echo 'V104_STAGE native_test_passed'
# Bounded, source-owned checkpoint diagnostics. Values reveal only
# whether exact test predicates passed, never private guest data.
log="$work/private-native.log"
count="$(grep -Ec '^V104_TRIAL_PASS trial=[0-9]{1,2}$' "$log" || true)"
save=0; grep -Fxq 'V104_ASYNC_SAVE route=1' "$log" && save=1 || true
cache=0; grep -Fxq 'V104_ASYNC_CACHE bounded=1' "$log" && cache=1 || true
sc=0; grep -Fxq 'V104_ASYNC_SYSCALL order=1 lines=1' "$log" && sc=1 || true
submit=0; grep -Fxq 'V104_ASYNC_SUBMIT route=1 request=1 mode=1 path=1 abi=1 prior=1' "$log" && submit=1 || true
terminal=0; grep -Eq '^PASS: [0-9]+ V104 recovered continuous original __start->IOS_OpenAsync request submit assertions; mode=owner trials=16 stop=0x805195ec$' "$log" && terminal=1 || true
echo "V104_SUCCESS_GATE count=$count save=$save cache=$cache sc=$sc submit=$submit terminal=$terminal"
for trial in $(seq 1 16); do
  grep -Fxq "V104_TRIAL_PASS trial=$trial" "$work/private-native.log"
done
test "$(grep -Ec '^V104_TRIAL_PASS trial=[0-9]{1,2}$' "$work/private-native.log")" -eq 16
grep -Fxq 'V104_ASYNC_SAVE route=1' "$work/private-native.log"
grep -Fxq 'V104_ASYNC_CACHE bounded=1' "$work/private-native.log"
grep -Fxq 'V104_ASYNC_SYSCALL order=1 lines=1' "$work/private-native.log"
grep -Fxq 'V104_ASYNC_SUBMIT route=1 request=1 mode=1 path=1 abi=1 prior=1' "$work/private-native.log"
grep -Eq '^PASS: [0-9]+ V104 recovered continuous original __start->IOS_OpenAsync request submit assertions; mode=owner trials=16 stop=0x805195ec$' "$work/private-native.log"
grep -E '^V104_ASYNC_(SAVE route=1|CACHE bounded=1|SYSCALL order=1 lines=1|SUBMIT route=1 request=1 mode=1 path=1 abi=1 prior=1)$' "$work/private-native.log" | sort -u
echo 'PASS: original Wii continuous __start constructed authentic IOS_OpenAsync request'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104'
"""
    # This is the final trailer of the V79-derived owner-local runner;
    # all authenticated fixture checks, generation, compile, and native
    # execution retain their original ordering and failure semantics.
    if not out.rstrip().endswith("echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805195EC stage=104'"):
        raise ValueError("V104 unexpected owner-runner trailer")
    return out[:out.index(anchor)]+success

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    result = derive(a.source.read_text(encoding="utf-8"))
    with a.output.open("x", encoding="utf-8") as f:
        f.write(result)

if __name__ == "__main__":
    main()
