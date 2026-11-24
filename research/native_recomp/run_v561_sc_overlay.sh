#!/usr/bin/env bash
set -euo pipefail
root="$(realpath "$1")"; here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf -- "$work"' EXIT; umask 077
mode=synthetic
args=()
if [[ $# == 2 ]]; then mode=owner; args=(--owner "$2"); fi
# Source-only patches; no game instructions written to source control.
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_native_lowmem_v63 apply_hid_state_v18 apply_syscall_pc_v26 apply_cache_events_v43; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo 'V561 patch failed';exit 1; }
done
python3 "$here/make_v561_sc_overlay_fixture.py" "$work/input" "${args[@]}"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY "${inc[@]}" "$here/offline_recompiler_driver_v6.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V561 driver build failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { grep -Ex 'SC translation overlay conflict|SC source ambiguous|SC source missing|SC vector return|SC vector control flow|SC overlay rejected|SC overlay analysis rejected|SC overlay instruction coverage rejected|SC overlay overlaps trusted span' "$work/generate.log" || true; echo 'V561 overlay translation failed';exit 1; }
# Never copy generated source into the original-free repository or logs.
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_sc_overlay_v561.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V561 native compilation failed';exit 1; }
timeout 15s "$work/native" "$work/input/vector.bin" "$mode" > "$work/native.log" 2>&1 || { echo 'V561 native execution failed';exit 1; }
grep -Ex "V561_SC_NATIVE owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) trials=32 vectors=32 refusal=3 fallback=0 boot_verified=0" "$work/native.log"
