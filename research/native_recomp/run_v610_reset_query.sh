#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 || $# == 2 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077
mode=synthetic;args=()
if [[ $# == 2 ]];then mode=owner;args=(--owner "$2");fi
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V610 source patch failed: $p";exit 1; }
done
python3 "$here/make_v610_reset_fixture.py" "$work/input" "${args[@]}"
g++ -std=c++20 -O2 -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V610 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V610 translation failed';exit 1; }
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_reset_query_v610.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V610 compile failed';exit 1; }
timeout 15s "$work/native" "$mode" > "$work/run.log" 2>&1 || { grep -E '^  what\(\):  (V610 line [0-9]+|arena reset read out of phase)$' "$work/run.log" || true; echo 'V610 execution failed';exit 1; }
grep -Ex "V610_RESET_NATIVE owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) trials=16 reads=32 returned=32 refusal=2 fallback=0 boot_verified=0" "$work/run.log"
