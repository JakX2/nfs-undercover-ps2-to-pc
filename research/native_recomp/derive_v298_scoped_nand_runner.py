#!/usr/bin/env python3
"""V298: run bounded owner-native NAND with only stale V178 observer scoped."""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
LINK='if g++ "$work/v296-harness.o" "$work/v294-generated.o" "$work/loader.o" \\'
DONE="echo 'V296_SERVICE_PROBE inspected=1'"
PRE=r'''
python3 "$V110_SOURCE_ROOT/derive_v298_scope_reply_observer.py"    "$work/v296-harness.cpp" "$work/v298-harness.cpp"
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label        -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include"        -c "$work/v298-harness.cpp" -o "$work/v298-harness.o"        > "$work/v298-compile.log" 2>&1; then
  echo 'V298_HARNESS_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py"     "$work/v298-compile.log" harness || true
  echo 'V298_HARNESS_STAGE compile=0'
  exit 1
fi
'''
V303_STAGE=r'''
# V303: entirely separate owner-private candidate. Do not overwrite the
# reduced baseline or the V294 restored four-function binary.
mkdir "$work/generated-v303"
if "$work/generator" "$work/private-v302.dol" "$work/generated-v303" owner \
    > "$work/v303-generate.log" 2>&1; then
  echo 'V303_HELPER_STAGE generate=1'
else
  echo 'V303_HELPER_STAGE generate=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/analyze_v301_nand_first_helper.py" \
     "$owner" "$work/v293-original.elf" "$work/private-v302.dol" \
     "$work/generated-v303/output.cpp" > "$work/v303-coverage-raw.log" 2>&1; then
  cat "$work/v303-coverage-raw.log"
  echo 'V303_HELPER_STAGE inspect=1'
else
  grep -Fx 'V301_HELPER_AUDIT verified=0' "$work/v303-coverage-raw.log" || true
  echo 'V303_HELPER_STAGE inspect=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/analyze_v303_helper_coverage.py" \
     "$work/v303-coverage-raw.log"; then
  echo 'V303_HELPER_STAGE coverage=1'
else
  echo 'V303_HELPER_STAGE coverage=0'
  exit 1
fi
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
    -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
    -c "$work/generated-v303/output.cpp" -o "$work/v303-generated.o" \
    > "$work/v303-compile.log" 2>&1; then
  echo 'V303_HELPER_STAGE compile=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" \
     "$work/v303-compile.log" generated || true
  echo 'V303_HELPER_STAGE compile=0'
  exit 1
fi
if g++ "$work/v298-harness.o" "$work/v303-generated.o" "$work/loader.o" \
      -o "$work/v303-native" > "$work/v303-link.log" 2>&1; then
  test -s "$work/v303-native" && test -x "$work/v303-native"
  echo 'V303_HELPER_STAGE link=1'
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" \
    "$work/v303-link.log" || true
  echo 'V303_HELPER_STAGE link=0'
  exit 1
fi
echo 'V303_HELPER_NATIVE_LINK verified=1'
# V306: read-only comparison of four original descendants of 0x804F2064.
# Never print the private function bytes or generated C++.
if python3 "$V110_SOURCE_ROOT/analyze_v306_helper_descendants.py"     "$owner" "$work/v293-original.elf" "$work/private-v302.dol"     "$work/generated-v303/output.cpp" > "$work/v306-coverage.log" 2>&1; then
  grep -Fx 'V306_COVERAGE_AUDIT verified=1' "$work/v306-coverage.log"
  grep -E '^V306_COVERAGE owner=1 targets=4 exact=[0-4] interior=[0-4] emitted=[0-4] dispatch=[0-4] missing=[0-4] partial=[0-4] unknown=[0-4]$' "$work/v306-coverage.log"
  grep -E '^V306_DESCENDANT pc=[0-9a-f]{8} kind=(exact|interior|unknown|ambiguous|invalid) base=[0-9a-f]{8} offset=[0-9]{1,5} words=[0-9]{1,5} present=[01] same=[0-9]{1,5} nop=[0-9]{1,5} blr=[0-9]{1,5} other=[0-9]{1,5} body=[01] dispatch=[01]$' "$work/v306-coverage.log"
  echo 'V306_DESCENDANT_STAGE inspected=1'
else
  grep -E '^V306_COVERAGE_ERROR reason=(authenticated_digest|fixture_geometry|function_size|original_span|cpp_geometry|span_geometry|invalid_target|input_io|other)$' "$work/v306-coverage.log" || true
  grep -Fx 'V306_COVERAGE_AUDIT verified=0' "$work/v306-coverage.log" || true
  echo 'V306_DESCENDANT_STAGE inspected=0'
  exit 1
fi
# V304: a separate native process executes the restored helper. No guest
# register changes or fake IOS replies. A timeout/crash is a diagnostic,
# not a successful boot or original NAND completion claim.
ulimit -c 0
set +e
timeout --signal=TERM --kill-after=3s 12s \
    "$work/v303-native" "$work/private-v302.dol" owner-callback "$owner" \
    > "$work/v304-native.log" 2>&1
v304_rc=$?
set -e
python3 "$V110_SOURCE_ROOT/analyze_v304_helper_exec.py" \
  "$work/v304-native.log" "$v304_rc"
echo 'V304_EXEC_ATTEMPT inspected=1'
# V307: attribute the V304 native abort against public C++ assertions only.
python3 "$V110_SOURCE_ROOT/analyze_v307_helper_abort.py"     "$work/v304-native.log" "$work/v298-harness.cpp" "$v304_rc"
echo 'V307_ABORT_CLASSIFIED inspected=1'
'''

AFTER=r'''
python3 "$V110_SOURCE_ROOT/analyze_v298_scope_native.py"    "$work/v295-native.log" "$work/v298-harness.cpp" "$v295_rc"
echo 'V298_RETIRED_OBSERVER inspected=1'
'''

def patch(source: str) -> str:
    if source.count(LINK)!=1 or source.count(DONE)!=1:
        raise ValueError("V298 owner-native compiler seam changed")
    staged=(source.replace(LINK,PRE+"\n"+
                           LINK.replace("v296-harness.o","v298-harness.o"),1)
                  .replace(DONE,DONE+"\n"+AFTER,1))
    aot_anchor="echo 'V294_RESTORED_AOT verified=1'"
    if staged.count(aot_anchor)!=1:
        raise ValueError("V301 authenticated helper AOT seam changed")
    helper_probe=(
        'python3 "$V110_SOURCE_ROOT/analyze_v301_nand_first_helper.py" '+
        '"$owner" "$work/v293-original.elf" "$work/private-v293.dol" '+
        '"$work/generated-v294/output.cpp"\n'+
        "echo 'V301_HELPER_AUDIT inspected=1'\n"+
        'python3 "$V110_SOURCE_ROOT/restore_v302_private_helper.py" '+
        '"$owner" "$work/v293-original.elf" "$work/private-v293.dol" '+
        '"$work/private-v302.dol"\n'+
        "echo 'V302_HELPER_CANDIDATE inspected=1'")
    staged=staged.replace(aot_anchor,aot_anchor+"\n"+helper_probe,1)
    v302_anchor="echo 'V302_HELPER_CANDIDATE inspected=1'"
    if staged.count(v302_anchor)!=1:
        raise ValueError("V303 private candidate seam changed")
    staged=staged.replace(v302_anchor,v302_anchor+"\n"+V303_STAGE,1)
    failure="  echo 'V295_BOUNDED_CANDIDATE inspected=0'"
    if staged.count(failure)!=1:
        raise ValueError("V298 native failure-classifier seam changed")
    # Print only a matched public C++ assertion label, never native logs.
    diagnostic=(
        '  python3 "$V110_SOURCE_ROOT/diagnose_v250_native_phase.py" '+
        '"$work/v295-native.log" "$work/v298-harness.cpp"\n'+
        '  python3 "$V110_SOURCE_ROOT/diagnose_v299_native_log.py" '+
        '"$work/v295-native.log" "$v295_rc" || true\n'+
        '  python3 "$V110_SOURCE_ROOT/analyze_v300_trace_hotspots.py" '+
        '"$work/v295-native.log" "$work/v298-harness.cpp" || true\n')
    return staged.replace(failure,diagnostic+failure,1)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="v298-") as td:
        prev=Path(td)/"v296.sh"
        r=subprocess.run(
            [sys.executable,str(HERE/"derive_v296_restored_nand_runner.py"),
             str(a.source),str(prev)],capture_output=True,text=True)
        if r.returncode:
            raise ValueError("V298 inherited owner-native runner changed")
        with a.output.open("x",encoding="utf-8") as dst:
            dst.write(patch(prev.read_text(encoding="utf-8")))
    return 0

if __name__=="__main__":
    sys.exit(main())
