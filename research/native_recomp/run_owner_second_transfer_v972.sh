#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_second_transfer_v971.py" "$dol" "$elf" "$work/owner_second_dispatch.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V955_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_second_transfer_v971.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$here" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_second_transfer_v971.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "generate_owner_second_transfer_v971.cpp";echo "V955_BUILD translator=0";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V955_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_second_transfer_v971.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie "${inc[@]}" "$here/test_owner_second_transfer_v972.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "test_owner_second_transfer_v972.cpp";echo "V955_BUILD native=0";exit 1; }
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" valid "$dol" > "$work/run.log" 2>&1 || {
      grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-3] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
      echo "V955_EXECUTION failed=1";exit 1;
    }
    grep -Fx 'V955_ACK_TRIAL verified=1 original_w1c=1 next_label=1 saved_fields=38 token=2' "$work/run.log"
  done
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" postack "$dol" > "$work/run.log" 2>&1 || {
      grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-4] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
      echo "V962_POST_EXECUTION failed=1";exit 1;
    }
    grep -Fx 'V955_ACK_TRIAL verified=1 original_w1c=1 next_label=1 saved_fields=38 token=2' "$work/run.log"
    grep -Ex 'V962_POST_ACK_RETURN original_helper_return=1 saved_fields=38 token_preserved=1 visits=[1-9][0-9]* handler_instruction_executed=0' "$work/run.log"
  done
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" time "$dol" > "$work/run.log" 2>&1 || {
      grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-4] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
      echo "V966_TIME_EXECUTION failed=1";exit 1;
    }
    grep -Ex 'V966_TIME_RETURN original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 visits=[1-9][0-9]* handler_instruction_executed=0' "$work/run.log"
  done
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" frontier "$dol" > "$work/run.log" 2>&1 || {
      grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-4] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
      echo "V968_FRONTIER_EXECUTION failed=1";exit 1;
    }
    grep -Ex 'V968_HANDLER_FRONTIER ordinal=([4-9]|[1-2][0-9]|3[0-2]) kind=[12] visits=[1-9][0-9]* token_preserved=1 saved_fields=38 call_executed=0' "$work/run.log"
  done
  admitted=0;returned=0;guards=0;incomplete=0
  for fixture in args queue-args active-args seeded-args; do
    for trial in {0..7}; do
      timeout 20s "$work/probe" "$trial" "$fixture" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        echo "V976_PROFILE_EXECUTION failed=1";exit 1;
      }
      if grep -Ex 'V976_GUARD_PROFILE seed=[0-3] profile=[0-7] lane=[1-5] ordinal=[0-9]{1,2} category=[1-6] stage=[14] depth=[0-8] time_return=[01] visits=[1-9][0-9]* original_guard_executed=0' "$work/run.log";then
        guards=$((guards+1));continue
      fi
      grep -Ex 'V973_TRANSFER_ARGS seeded=[01] profile=[0-7] out_one=[01] in_three=[01] out_mapped=[01] in_mapped=[01] callback=[01] command_zero=[01] idle=[01] type=[01]' "$work/run.log"
      grep -Ex 'V976_ARG_PROFILE seed=[0-3] profile=[0-7] admissible=[01] original_transfer_executed=0' "$work/run.log"
      if ! grep -qE '^V976_ARG_PROFILE seed=[1-3] profile=[0-7] admissible=1 original_transfer_executed=0$' "$work/run.log";then
        incomplete=$((incomplete+1));continue
      fi
      admitted=$((admitted+1))
      case "$fixture" in queue-args) lane=queue-transfer;; active-args) lane=active-transfer;; seeded-args) lane=transfer;; *) exit 1;; esac
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        echo "V972_TRANSFER_EXECUTION failed=1";exit 1;
      }
      grep -Ex 'V972_TRANSFER_RETURN original_transfer=1 idle=[01] token=[23] pending=[01] visits=[1-9][0-9]* reads=[0-9]+ writes=[0-9]+ saved_fields=38 handler_instruction_executed=0' "$work/run.log"
      returned=$((returned+1))
    done
  done
  [[ $((admitted+guards+incomplete)) == 32 && "$returned" == "$admitted" ]]
  echo "V976_PROFILE_CENSUS mode=$mode classified=32 guarded=$guards incomplete=$incomplete admitted=$admitted returned=$returned fallback=0 continuous_boot=0"
  for bad in bad-frame bad-pi; do
    rc=0;timeout 20s "$work/probe" 0 "$bad" "$dol" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    if [[ "$bad" == bad-frame ]];then grep -Fx 'V946_FRAME_REFUSAL saved_gpr=1' "$work/run.log";else grep -Fx 'V946_PI_REFUSAL wrong_value=1' "$work/run.log";fi
  done
  echo "V955_OWNER_ACK mode=$mode valid=8 original_dispatcher=8 original_w1c=8 token_preserved=8 negative=2 fallback=0 continuous_boot=0"
  echo "V962_OWNER_POST_ACK mode=$mode valid=8 original_helper_return=8 fallback=0 continuous_boot=0"
  echo "V966_OWNER_TIME mode=$mode valid=8 original_time_return=8 fallback=0 continuous_boot=0"
  echo "V968_OWNER_FRONTIER mode=$mode valid=8 guarded_dependency=8 fallback=0 continuous_boot=0"
  # A profile may reach a different guarded dependency; never label it a transfer return.
done
