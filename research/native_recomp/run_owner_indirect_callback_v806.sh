#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_indirect_callback_v806.py" "$dol" "$elf" "$work/owner_indirect_callback.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V806_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_indirect_callback_v806.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_indirect_callback_v806.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V806_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V806_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_indirect_callback_v806.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_indirect_callback_v806.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V806_NATIVE_BUILD failed=1";exit 1; }
  for trial in {0..7}; do
    timeout 20s "$work/probe" valid "$trial" > "$work/run.log" 2>&1 || {
      grep -Ex 'V806_CALLBACK_FAULT kind=[1-8] line=[0-9]{1,4} stage=[0-6] witness=[0-4] entries=[0-3] polls=[0-2] visits=[0-9]{1,2}' "$work/run.log" || true
      echo "V806_NATIVE_EXECUTION failed=1";exit 1;
    }
    grep -Fx 'V806_OWNER_INDIRECT_CALLBACK dispatch=1 original_prologue=1 save_return=1 stack_writes=8 continuation_executed=0 fallback=0 continuous_boot=0' "$work/run.log"
  done
  for spec in identity:1 ctr:2 corrupt:3; do
    rc=0
    timeout 20s "$work/probe" "${spec%:*}" 0 > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V806_CALLBACK_REFUSAL kind=${spec#*:}" "$work/run.log"
  done
  echo "V806_CALLBACK_MODE mode=$mode valid=8 refused=3"
done
