#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_hollywood_mmio_v62;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V650 source patch failed: $p";exit 1; }
done
python3 "$here/make_v650_report_fixture.py" "$2" "$3" "$work/input"
python3 "$here/apply_report_table_v594.py" "$root" "$2" "$3"
python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native
g++ -std=c++20 -O2 -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V650 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V650 translation failed';exit 1; }
python3 "$here/make_v650_report_fixture.py" "$2" "$3" "$work/generated" --trace
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_report_outer_v650.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V650 compile failed';exit 1; }
rc=0
ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$work/native" > "$work/run.log" 2>&1 || rc=$?
grep -Ex 'V650_REPORT_TRIAL n=[0-9]{1,2} class=[0-9]{1,2} calls=10 getters=6 computed=[01]|V650_REPORT_FAILURE trial=[0-9]{1,2} (line=[0-9]{1,4} reason=[0-9] stage=[0-3] reports=[0-9]{1,2} getters=[0-6] mask=[0-9]{1,3}|kind=exception)' "$work/run.log" || true
[[ "$rc" == 0 ]] || { echo "V650 execution failed rc=$rc";exit 1; }
grep -Fx 'V650_REPORT_NATIVE trials=16 returned=16 calls=160 getters=96 output_backend=0 fallback=0 complete_image=0' "$work/run.log"
