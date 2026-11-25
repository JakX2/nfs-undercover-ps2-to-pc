#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_status_w1c_v917.py" "$dol" "$elf" "$work/owner_restore_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V917_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_status_w1c_v917.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_branch_v917.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V917_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V917_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_status_w1c_v917.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_status_w1c_v917.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" test_owner_status_w1c_v917.cpp; echo "V917_NATIVE_BUILD failed=1";exit 1; }
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" 0 > "$work/run.log" 2>&1 || {
      grep -Ex 'V917_STATUS_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-2] visits=[0-9]{1,2} reads=[01] writes=[01] guard=[0-5] device=[0-9]' "$work/run.log" || true
      grep -Ex 'V913_ARM_NATIVE visit=[0-9]{1,2} mem1=[01] si=[01] aligned=[01] base_class=[1-4]' "$work/run.log" || true
      echo 'V917_NATIVE_EXECUTION failed=1';exit 1;
    }
    changed=1; if (( trial>=4 )); then changed=0; fi
    grep -Ex "V917_OWNER_HANDLER_BOUNDARY changed=$changed first_taken=$((trial%2)) next=(7|8|12) words=[0-9]{2} ram_reads=[0-9]{1,2} ram_writes=[01] branches=[0-9]{1,2} compares=[0-9]{1,2} original_call_executed=0 fallback=0 continuous_boot=0" "$work/run.log"
  done
  for kind in 1 2 3 4 5 6 7 8; do
    rc=0
    timeout 20s "$work/probe" 0 "$kind" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V917_STATUS_REFUSAL kind=$kind" "$work/run.log"
  done
  echo "V917_STATUS_MODE mode=$mode valid=8 refused=8"
done
