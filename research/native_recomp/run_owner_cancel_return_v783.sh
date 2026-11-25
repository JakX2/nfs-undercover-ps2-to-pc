#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
unset NWII_WALLTB NWII_SAMPLE
ulimit -c 0
python3 "$here/prepare_owner_head_v782.py" "$dol" "$elf" "$work/owner_head_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V764_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_head_v782.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_head_v764.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V764_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V764_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_head_v782.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_cancel_return_v783.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V764_NATIVE_BUILD failed=1";exit 1; }
  timeout 20s "$work/probe" valid > "$work/run.log" 2>&1 || {
    grep -Ex 'V783_FAULT kind=[1-8] line=[0-9]{1,4} lane=[0-4] visits=[0-9]{1,3} stage=[0-4] route=[0-8] queue=[0-5] mismatch=[0-6]' "$work/run.log" || true
    echo "V764_NATIVE_EXECUTION failed=1";exit 1;
  }
  grep -Ex 'V785_CLEAR_ORDER deferred=[0-6] head=6' "$work/run.log"
  grep -Fx 'V783_OWNER_CANCEL_RETURN valid=14 inactive=2 middle=2 tail=2 singleton=2 head=6 fallback=0 continuous_boot=0' "$work/run.log"
  for fault in gpr link tick; do
    rc=0
    timeout 20s "$work/probe" "$fault" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    case "$fault" in gpr) kind=1;; link) kind=2;; tick) kind=3;; esac
    grep -Fx "V783_REFUSAL kind=$kind" "$work/run.log"
  done
  echo "V783_MODE mode=$mode valid=14 refused=3"
done
