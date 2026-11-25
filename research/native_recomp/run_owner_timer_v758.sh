#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
unset NWII_WALLTB NWII_SAMPLE
ulimit -c 0
python3 "$here/prepare_owner_timer_v758.py" "$dol" "$elf" "$work/owner_timer_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V758_EMITTER_PATCH failed=1";exit 1; }
done
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_timer_v758.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V758_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V758_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_timer_v758.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_timer_v758.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V758_NATIVE_BUILD failed=1";exit 1; }
  timeout 20s "$work/probe" valid > "$work/run.log" 2>&1 || {
    grep -Ex 'V758_TIMER_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-4] visits=[0-9]{1,2} stage=[0-2]' "$work/run.log" || true
    echo "V758_NATIVE_EXECUTION failed=1";exit 1;
  }
  grep -Ex 'V758_OWNER_TIMER_AOT valid=8 roots=[1-3] native_returns=8 modeled_dec=1 irq_delivery=0 fallback=0 continuous_boot=0' "$work/run.log"
  rc=0
  timeout 20s "$work/probe" corrupt > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V758_TIMER_REFUSAL timer_state_corruption=1' "$work/run.log"
  echo "V758_MODE mode=$mode valid=8 refused=1"
done
