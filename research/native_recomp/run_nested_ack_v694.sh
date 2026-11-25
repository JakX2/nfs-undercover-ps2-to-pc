#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
python3 "$here/apply_verified_elf_spans_v6.py" "$root"
python3 "$here/apply_function_root_v443.py" "$root"
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_exact_dispatch_v445.py" "$root"
python3 "$here/apply_native_tick_v438.py" "$root"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_nested_ack_v694.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode"
  python3 "$here/prepare_synthetic_nested_v694.py" "$work/$mode" "$work/$mode/include"
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label \
    -fno-pie -no-pie -I"$work/$mode/include" -I"$root/nWiiRuntime/include" "$here/test_nested_ack_v694.cpp" "$work/$mode"/*.cpp -o "$work/probe"
  PYTHONPATH="$here" python3 - "$work/probe" "$mode" <<'PY'
import sys,subprocess
from audit_v672_si_ack_route import EVENTS,RESULT
first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,4)]
nested=[f'V693_SI_NESTED_STAGE n={i}'.encode() for i in range(1,4)]
base=EVENTS[:1]+first+second[:2]
expected={'nested':(0,base+nested[:2]+[b'V693_SI_NESTED_ACK n=1']+EVENTS[1:]+[RESULT]),
          'second':(0,base+nested+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]),
          'after':(0,base+nested+second[2:]+EVENTS[1:]+[RESULT]),
          'deeper':(126,base+nested[:2]+[b'V693_SI_NESTED_CALL ordinal=1 kind=1',b'V693_SI_NESTED_INVALID reason=4 stage=2 trace=0'])}
for mode,(rc,lines) in expected.items():
    r=subprocess.run([sys.argv[1],mode],capture_output=True,timeout=15)
    if r.returncode!=rc or r.stdout.splitlines()!=lines or r.stderr:
        print(r.stdout.decode(),r.stderr.decode());raise SystemExit(1)
print(f'V694_NESTED_AOT mode={sys.argv[2]} cases=4 actual_guest_store=1 nested_refused=1 fallback=0 original_execution=0')
PY
done
