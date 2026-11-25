#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_scheduler_v722.py" "$dol" "$elf" "$work/owner_scheduler_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V722_EMITTER_PATCH failed=1";exit 1; }
done
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_scheduler_v722.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V722_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V722_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_scheduler_v722.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_scheduler_v722.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V722_NATIVE_BUILD failed=1";exit 1; }
  timeout 20s "$work/probe" valid > "$work/run.log" 2>&1 || {
    grep -Ex 'V722_SCHEDULER_FAULT kind=[1-9] line=[0-9]{1,4} stage=[0-3] entries=[0-6] visits=[0-9]{1,3} outer=[0-9]{1,2}|V722_SCHEDULER_MISMATCH return=[01] counter=[01]' "$work/run.log" || true
    echo "V722_NATIVE_EXECUTION failed=1";exit 1;
  }
  grep -Fx 'V722_OWNER_SCHEDULER_AOT valid=6 original_enable=6 original_resched=6 original_switch=0 fallback=0 continuous_boot=0' "$work/run.log"
  rc=0
  timeout 20s "$work/probe" switch > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V722_SWITCH_REFUSAL guarded_tail=1 original_switch=0' "$work/run.log"
  echo "V722_MODE mode=$mode valid=6 switch_refused=1"
done
