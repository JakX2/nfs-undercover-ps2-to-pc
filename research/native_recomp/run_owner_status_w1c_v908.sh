#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_status_w1c_v908.py" "$dol" "$elf" "$work/owner_restore_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V908_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_status_w1c_v908.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_branch_v908.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V908_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V908_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_status_w1c_v908.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_status_w1c_v908.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V908_NATIVE_BUILD failed=1";exit 1; }
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" 0 > "$work/run.log" 2>&1 || {
      grep -Ex 'V908_STATUS_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-2] visits=[0-9]{1,2} reads=[01] writes=[01] guard=[0-5] device=[0-9]' "$work/run.log" || true
      echo 'V908_NATIVE_EXECUTION failed=1';exit 1;
    }
    changed=1; if (( trial>=4 )); then changed=0; fi
    grep -Fx "V908_OWNER_STATUS_W1C prefix_words=14 native_gpr=1 indexed_ram=1 reads=1 writes=1 w1c=1 changed=$changed follow_held=1 branch_taken=$((trial%2)) arm_words=$((5-2*(trial%2))) arm_reads=$((1-trial%2)) fallback=0 continuous_boot=0" "$work/run.log"
  done
  for kind in 1 2 3 4 5 6 7; do
    rc=0
    timeout 20s "$work/probe" 0 "$kind" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V908_STATUS_REFUSAL kind=$kind" "$work/run.log"
  done
  echo "V908_STATUS_MODE mode=$mode valid=8 refused=7"
done
