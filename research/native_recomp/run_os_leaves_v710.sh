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
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_os_leaves_v710.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode"
  python3 "$here/prepare_synthetic_os_leaves_v710.py" "$work/$mode" "$work/$mode/include"
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label \
    -fno-pie -no-pie -I"$work/$mode/include" -I"$root/nWiiRuntime/include" "$here/test_os_leaves_v710.cpp" "$work/$mode"/*.cpp -o "$work/probe"
  PYTHONPATH="$here" python3 - "$work/probe" "$mode" <<'PY'
import sys,subprocess,os
from audit_v699_si_postack import STAGE,END
from audit_v709_os_leaves import LEAVES
from audit_v672_si_ack_route import EVENTS,RESULT
first=[f'V680_SI_HELPER_STAGE n={i}'.encode() for i in range(1,4)]
second=[f'V688_SI_SECOND_STAGE n={i}'.encode() for i in range(1,4)]
nested=[f'V693_SI_NESTED_STAGE n={i}'.encode() for i in range(1,4)]
base=EVENTS[:1]+first+second[:2]+[b'V688_SI_SECOND_ACK n=1']+EVENTS[1:]+[RESULT]
expected={'stop':(0,base),
          'continue':(0,base+[STAGE]+nested[:2]+LEAVES+nested[2:]+second[2:]+[END]),
          'disabled':(126,base+[STAGE]+nested[:2]+[b'V693_SI_NESTED_CALL ordinal=1 kind=1',b'V693_SI_NESTED_INVALID reason=4 stage=2 trace=0']),
          'wrong-order':(126,base+[STAGE]+nested[:2]+[b'V693_SI_NESTED_CALL ordinal=2 kind=1',b'V693_SI_NESTED_INVALID reason=4 stage=2 trace=0'])}
for mode,(rc,lines) in expected.items():
    env=dict(os.environ);env.pop('UNDERCOVER_V699_SI_POSTACK',None)
    env.pop('UNDERCOVER_V709_OS_LEAVES',None)
    if mode!='stop':env['UNDERCOVER_V699_SI_POSTACK']='1'
    if mode in ('continue','wrong-order'):env['UNDERCOVER_V709_OS_LEAVES']='1'
    r=subprocess.run([sys.argv[1],mode],capture_output=True,timeout=15,env=env)
    if r.returncode!=rc or r.stdout.splitlines()!=lines or r.stderr:
        print(r.stdout.decode(),r.stderr.decode());raise SystemExit(1)
print(f'V710_OS_LEAVES_AOT mode={sys.argv[2]} cases=4 actual_guest_read=1 actual_guest_store=1 postack_leaf_returns=3 wrong_order_refused=1 fallback=0 original_execution=0')
PY
done
