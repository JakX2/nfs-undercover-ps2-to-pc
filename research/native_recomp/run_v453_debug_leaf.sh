#!/usr/bin/env bash
set -euo pipefail
if [[ $# != 1 && $# != 3 ]]; then echo 'usage: run_v453_debug_leaf.sh NWII_ROOT [OWNER_DOL OWNER_ELF]' >&2; exit 2; fi
root="$(realpath "$1")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ -z "$(git -C "$root" status --porcelain)" ]]
umask 077
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
unset NWII_TRACE_CALLS NWII_TRACE_ONLY NWII_WALLTB
args=()
owner=0
if [[ $# == 3 ]]; then args=(--owner "$2" --elf "$3"); owner=1; fi
show_synthetic_failure(){
  if [[ "$owner" == 0 ]]; then tail -n 50 "$1"; fi
}
python3 "$here/prepare_v453_debug_leaf.py" "$work/debug.dol" "${args[@]}"
if [[ ! -f "$work/debug.dol" ]]; then
  echo "V453_DEBUG_RESULT owner=$owner native=0 reason=nonleaf boot_verified=0"
  exit 0
fi
words=$(( ($(stat -c '%s' "$work/debug.dol")-256)/4 ))
(( words>=1 && words<=32 ))
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root" > "$work/patch.log" 2>&1
python3 "$here/apply_native_tick_v438.py" "$root" >> "$work/patch.log" 2>&1
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 -Wno-unused-variable -Wno-sign-compare "${inc[@]}" \
  "$here/generate_debug_leaf_v453.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo 'V453_DEBUG_FAILURE stage=generator_compile'; show_synthetic_failure "$work/build.log"; exit 1; }
for mode in nonsplit split; do
  dir="$work/$mode";mkdir "$dir"
  "$work/generator" "$work/debug.dol" "$dir" "$mode" > "$work/generate.log" 2>&1 || { echo "V453_DEBUG_FAILURE stage=generate mode=$mode"; show_synthetic_failure "$work/generate.log"; exit 1; }
  flags=()
  if [[ "$mode" == split ]]; then flags=(-DV453_SPLIT -I"$dir"); fi
  g++ -std=c++20 -O1 -Wall -Wextra -Wno-unused-label -Wno-unused-parameter -Wno-unused-variable \
    -Wno-sign-compare -pthread -fsanitize=address,undefined -fno-pie -no-pie "${inc[@]}" "${flags[@]}" \
    "$here/test_native_debug_leaf_v453.cpp" "$dir"/*.cpp \
    "$root/nWiiRuntime/src/core/os_hle_stubs.cpp" "$root/nWiiRuntime/src/hw/mmio_dispatcher.cpp" \
    "$root/nWiiRuntime/src/hw/hw_pi.cpp" "$root/nWiiRuntime/src/hw/hw_ipc.cpp" -o "$dir/native" \
    > "$work/compile.log" 2>&1 || { echo "V453_DEBUG_FAILURE stage=compile mode=$mode"; show_synthetic_failure "$work/compile.log"; exit 1; }
  timeout 20s "$dir/native" "$words" > "$work/native.log" 2>&1 || { echo "V453_DEBUG_FAILURE stage=run mode=$mode"; show_synthetic_failure "$work/native.log"; exit 1; }
  marker="V453_DEBUG_NATIVE runs=4 words=$words return=1 abi=1 fallback=0 boot_verified=0"
  [[ "$(grep -Fxc "$marker" "$work/native.log")" == 1 ]]
  echo "V453_DEBUG_MODE mode=$mode owner=$owner runs=4 return=1 abi=1 fallback=0"
done
echo "V453_DEBUG_RESULT owner=$owner native=1 modes=2 runs=8 boot_verified=0"
