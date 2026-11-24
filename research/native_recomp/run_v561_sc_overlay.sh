#!/usr/bin/env bash
set -euo pipefail
root="$(realpath "$1")"; here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf -- "$work"' EXIT; umask 077
mode=synthetic
args=()
if [[ $# == 2 ]]; then mode=owner; args=(--owner "$2"); fi
# Source-only patches; no game instructions written to source control.
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_native_lowmem_v63 apply_hid_state_v18 apply_syscall_pc_v26 apply_cache_events_v561; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V561 patch failed: $patch";exit 1; }
done
g++ -std=c++20 -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-pie -no-pie -I"$root/nWiiRuntime/include" "$here/test_sc_overlay_geometry_v567.cpp" -o "$work/geometry"
"$work/geometry"
python3 "$here/make_v561_sc_overlay_fixture.py" "$work/input" "${args[@]}"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY "${inc[@]}" "$here/offline_recompiler_driver_v6.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V561 driver build failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { grep -Ex 'SC translation overlay conflict|SC source ambiguous|SC source missing|SC source overlap|SC section geometry|SC vector return|SC vector control flow|SC overlay rejected|SC overlay analysis rejected|SC overlay instruction coverage rejected|SC overlay overlaps trusted span' "$work/generate.log" || true; echo 'V561 overlay translation failed';exit 1; }
# Never copy generated source into the original-free repository or logs.
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_sc_overlay_v561.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V561 native compilation failed';exit 1; }
timeout 15s "$work/native" "$work/input/vector.bin" "$mode" > "$work/native.log" 2>&1 || { echo 'V561 native execution failed';exit 1; }
grep -Ex "V561_SC_NATIVE owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) trials=32 vectors=32 refusal=3 fallback=0 boot_verified=0" "$work/native.log"

# V568: verify the native flush->SC->RFI->BLR path in the same pinned runtime.
python3 "$here/apply_syscall_transfer_v461.py" "$root" > "$work/transfer.log" 2>&1 || { echo 'V568 syscall transfer patch failed';exit 1; }
# Rebuild the offline driver after editing its emitter.
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY "${inc[@]}" "$here/offline_recompiler_driver_v6.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/driver-flush" > "$work/flush-build.log" 2>&1 || { echo 'V568 driver build failed';exit 1; }
python3 "$here/make_v561_sc_overlay_fixture.py" "$work/flush-input" --flush "${args[@]}"
mkdir "$work/flush-generated"
"$work/driver-flush" "$work/flush-input/fixture.dol" "$work/flush-input/symbols.csv" "$work/flush-generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/flush-generate.log" 2>&1 || { echo 'V568 flush translation failed';exit 1; }
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/flush-generated" -I"$work/flush-generated/nWiiRuntime/include" \
  "$here/test_native_sc_flush_v568.cpp" "$work/flush-generated"/*.cpp -o "$work/native-flush" > "$work/flush-compile.log" 2>&1 || { echo 'V568 flush compilation failed';exit 1; }
timeout 15s "$work/native-flush" "$work/flush-input/vector.bin" "$mode" > "$work/flush-native.log" 2>&1 || { grep -E '^  what\(\):  SC overlay line [0-9]+$' "$work/flush-native.log" || true; echo 'V568 flush execution failed';exit 1; }
grep -Ex "V568_SC_FLUSH owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) trials=32 lines=128 vectors=32 refusal=3 stop=1 fallback=0 boot_verified=0" "$work/flush-native.log"

# V570 uses the same translated flush and original vector, with the explicit one-shot route.
python3 "$here/patch_sc_trace_v570.py" "$work/flush-generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/flush-generated" --vector "$work/flush-input/vector.bin"
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/flush-generated" -I"$work/flush-generated/nWiiRuntime/include" \
  "$here/test_native_sc_route_v570.cpp" "$work/flush-generated"/*.cpp -o "$work/native-route" > "$work/route-compile.log" 2>&1 || { echo 'V570 route compilation failed';exit 1; }
timeout 15s "$work/native-route" "$work/flush-input/vector.bin" "$mode" > "$work/route-native.log" 2>&1 || { grep -E '^  what\(\):  (SC overlay line [0-9]+|V570 boot SC route rejected)$' "$work/route-native.log" || true; echo 'V570 route execution failed';exit 1; }
grep -Ex "V570_SC_ROUTE owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) trials=32 lines=128 vectors=32 refusal=6 delegated=1 stop=1 direct_only=30 fallback=0 boot_verified=0" "$work/route-native.log"

# V578: actual binding header spans two translation units, like IOS + observer.
python3 "$here/make_v561_sc_overlay_fixture.py" "$work/binding-input" --flush --binding "${args[@]}"
mkdir "$work/binding-generated"
"$work/driver-flush" "$work/binding-input/fixture.dol" "$work/binding-input/symbols.csv" "$work/binding-generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/binding-generate.log" 2>&1 || { echo 'V578 binding translation failed';exit 1; }
python3 "$here/patch_sc_trace_v570.py" "$work/binding-generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/binding-generated" --vector "$work/binding-input/vector.bin"
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/binding-input" -I"$work/binding-generated" -I"$work/binding-generated/nWiiRuntime/include" \
  "$here/test_native_sc_binding_v578.cpp" "$here/test_native_sc_binding_ios_v578.cpp" "$work/binding-generated"/*.cpp -o "$work/native-binding" > "$work/binding-compile.log" 2>&1 || { echo 'V578 binding compilation failed';exit 1; }
for trial in normal disabled installed source unarmed irq caller return repeat; do
  rc=0;on=1
  [[ "$trial" != disabled ]] || on=0
  UNDERCOVER_V574_SC="$on" timeout 15s "$work/native-binding" "$trial" > "$work/binding-native.log" 2>&1 || rc=$?
  if [[ "$trial" == normal ]]; then
    [[ "$rc" == 0 ]]; grep -Fx 'V578_SC_BINDING native=1 shared=1 delegated=1 lines=4 fallback=0 boot_verified=0' "$work/binding-native.log"
  elif [[ "$trial" == disabled ]]; then
    [[ "$rc" == 0 ]]; grep -Fx 'V578_SC_BINDING disabled=1 delegated=2 shared=1 fallback=0' "$work/binding-native.log"
  else
    [[ "$rc" == 113 ]]; grep -Fxq 'V574_DSP_SC_INVALID rejected=1' "$work/binding-native.log"
  fi
done
echo "V578_SC_BINDING_RESULT owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) native=1 shared=1 disabled=1 refused=7 fallback=0 boot_verified=0"

# V598: large native flush loop and two independent caller-specific SC routes.
python3 "$here/make_v561_sc_overlay_fixture.py" "$work/arena-input" --flush --binding --arena "${args[@]}"
mkdir "$work/arena-generated"
"$work/driver-flush" "$work/arena-input/fixture.dol" "$work/arena-input/symbols.csv" "$work/arena-generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/arena-generate.log" 2>&1 || { echo 'V598 arena translation failed';exit 1; }
python3 "$here/patch_sc_trace_v570.py" "$work/arena-generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/arena-generated" --vector "$work/arena-input/vector.bin"
python3 "$here/prepare_v598_arena_fixture.py" "$work/arena-generated"
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/arena-input" -I"$work/arena-generated" -I"$work/arena-generated/nWiiRuntime/include" \
  "$here/test_native_arena_sc_v598.cpp" "$work/arena-generated"/*.cpp -o "$work/native-arena" > "$work/arena-compile.log" 2>&1 || { python3 "$here/classify_v599_arena_compile.py" "$work/arena-compile.log"; echo 'V598 arena compilation failed';exit 1; }
timeout 30s "$work/native-arena" "$mode" > "$work/arena-native.log" 2>&1 || { grep -E '^  what\(\):  (V598 line [0-9]+|V598 arena SC pair rejected|V570 boot SC route rejected|arena cache sequence rejected)$' "$work/arena-native.log" || true;echo 'V598 arena execution failed';exit 1; }
grep -Ex "V598_ARENA_SC owner=$( [[ "$mode" == owner ]] && echo 1 || echo 0 ) lanes=2 flush_lines=16384 vectors=2 refusal=8 fallback=0 boot_verified=0" "$work/arena-native.log"
