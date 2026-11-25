#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT; umask 077
python3 "$here/prepare_owner_leaf_v714.py" "$dol" "$elf" "$work/owner_leaf_input.h"
python3 "$here/apply_verified_elf_spans_v6.py" "$root"
python3 "$here/apply_function_root_v443.py" "$root"
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_exact_dispatch_v445.py" "$root"
python3 "$here/apply_native_tick_v438.py" "$root"
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_leaf_v714.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/compile.log" 2>&1 || { echo "V714_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V714_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_leaf_v714.py" "$dol" "$elf" "$work/$mode" --include "$work/$mode/include"
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label \
    -fno-pie -no-pie -I"$work" -I"$work/$mode/include" -I"$root/nWiiRuntime/include" "$here/test_owner_leaf_v714.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/compile.log" 2>&1 || { echo "V714_NATIVE_BUILD failed=1";exit 1; }
  for tick in 100 0x100000064 0xfffffff4; do
    timeout 15s env -u NWII_WALLTB "$work/probe" valid "$tick" > "$work/valid.log" 2>&1 || { echo "V714_NATIVE_EXECUTION failed=1";exit 1; }
    grep -Fx 'V714_LEAF_AOT roots=3 mtmsr=2 timebase=1 inner_callbacks=0 native_return=3 fallback=0' "$work/valid.log"
  done
  rc=0
  timeout 15s env -u NWII_WALLTB "$work/probe" corrupt 100 > "$work/corrupt.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V714_REFUSAL reason=4' "$work/corrupt.log"
  echo "V714_OWNER_LEAF_AOT mode=$mode valid=3 refused=1 original_leaves=3 continuous_boot=0 fallback=0"
done
