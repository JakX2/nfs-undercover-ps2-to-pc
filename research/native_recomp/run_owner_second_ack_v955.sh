#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_second_ack_v955.py" "$dol" "$elf" "$work/owner_second_dispatch.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V955_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_second_ack_v955.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$here" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_second_ack_v955.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "generate_owner_second_ack_v955.cpp";echo "V955_BUILD translator=0";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V955_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_second_ack_v955.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie "${inc[@]}" "$here/test_owner_second_ack_v955.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "test_owner_second_ack_v955.cpp";echo "V955_BUILD native=0";exit 1; }
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" valid "$dol" > "$work/run.log" 2>&1 || {
      grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-3] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
      echo "V955_EXECUTION failed=1";exit 1;
    }
    grep -Fx 'V955_ACK_TRIAL verified=1 original_w1c=1 next_label=1 saved_fields=38 token=2' "$work/run.log"
  done
  for bad in bad-frame bad-pi; do
    rc=0;timeout 20s "$work/probe" 0 "$bad" "$dol" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    if [[ "$bad" == bad-frame ]];then grep -Fx 'V946_FRAME_REFUSAL saved_gpr=1' "$work/run.log";else grep -Fx 'V946_PI_REFUSAL wrong_value=1' "$work/run.log";fi
  done
  echo "V955_OWNER_ACK mode=$mode valid=8 original_dispatcher=8 original_w1c=8 token_preserved=8 negative=2 fallback=0 continuous_boot=0"
done
