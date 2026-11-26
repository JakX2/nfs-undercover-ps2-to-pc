#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_second_shared_v988.py" "$dol" "$elf" "$work/owner_second_dispatch.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V955_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_second_shared_v988.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$here" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_second_alarm_v985.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "generate_owner_second_alarm_v985.cpp";echo "V955_BUILD translator=0";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V955_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_second_shared_v988.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie "${inc[@]}" "$here/test_owner_second_shared_v988.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "test_owner_second_shared_v988.cpp";echo "V955_BUILD native=0";exit 1; }
  for trial in {0..7}; do
    timeout 20s "$work/probe" "$trial" postack "$dol" > "$work/run.log" 2>&1 || {
      grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
      exit 1;
    }
    grep -Ex 'V962_POST_ACK_RETURN original_helper_return=1 saved_fields=38 token_preserved=1 visits=[1-9][0-9]* handler_instruction_executed=0' "$work/run.log"
  done
  for lane in active-success seeded-success; do
    for trial in {0..3}; do
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        echo 'V988_SHARED_EXECUTION failed=1';exit 1;
      }
      grep -Ex 'V988_SHARED_TIME_RETURN original_time=1 leaves=3 unchanged_msr=2 visits=[1-9][0-9]* token_preserved=1 saved_fields=38' "$work/run.log"
      grep -Ex 'V988_SUCCESS_HELPER_RETURN seed=[23] profile=[0-3] original_helper_return=1 shared_time=1 visits=[1-9][0-9]* token_preserved=1 saved_fields=38 handler_instruction_executed=0' "$work/run.log"
    done
  done
  for lane in active-frontier seeded-frontier; do
    for trial in {0..3}; do
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        echo 'V992_SUCCESS_FRONTIER_EXECUTION failed=1';exit 1;
      }
      grep -Ex 'V988_SUCCESS_HELPER_RETURN seed=[23] profile=[0-3] original_helper_return=1 shared_time=1 visits=[1-9][0-9]* token_preserved=1 saved_fields=38 handler_instruction_executed=0' "$work/run.log"
      grep -Ex 'V992_SUCCESS_FRONTIER seed=[23] profile=[0-3] lane=[1-5] ordinal=[0-9]{1,2} kind=[1-6] time_return=[01] callback_candidate=[01] visits=[1-9][0-9]* token_preserved=1 saved_fields=38 call_executed=0' "$work/run.log"
      grep -Ex 'V976_ARG_PROFILE seed=[23] profile=[0-3] admissible=[01] original_transfer_executed=0' "$work/run.log" || true
    done
  done
  for lane in active-error seeded-error active-error-cold seeded-error-cold; do
    case "$lane" in active-*) seed=2;; *) seed=3;; esac
    case "$lane" in *-cold) prior=1;; *) prior=0;; esac
    for trial in {4..7}; do
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        echo "V1013_ERROR_EXECUTION failed=1 seed=$seed prior_absent=$prior profile=$trial";exit 1;
      }
      test "$(grep -Fxc 'V955_ACK_TRIAL verified=1 original_w1c=1 next_label=1 saved_fields=38 token=2' "$work/run.log")" = 1
      pattern="V1013_ERROR_CENSUS seed=$seed prior_absent=$prior profile=$trial (helper_return=1 shared_time=[01] lane=0 ordinal=0 kind=0 depth=0|helper_return=0 shared_time=[01] lane=[1-5] ordinal=[0-9]{1,2} kind=[1-6] depth=[0-8]) entries=[1-9][0-9]{0,3} returns=[1-9][0-9]{0,3} msr=[0-9]{1,4} visits=[1-9][0-9]{0,3} token_preserved=1 saved_fields=38 boundary_executed=0 continuous_boot=0"
      test "$(grep -Exc "$pattern" "$work/run.log")" = 1
      grep -Ex "$pattern" "$work/run.log"
    done
  done
  echo "V1013_OWNER_ERROR_CENSUS mode=$mode classified=16 fallback=0 continuous_boot=0"
  for lane in active-error seeded-error active-error-cold seeded-error-cold; do
    case "$lane" in active-*) seed=2;; *) seed=3;; esac
    case "$lane" in *-cold) prior=1;; *) prior=0;; esac
    for trial in {4..7}; do
      timeout 20s "$work/probe" "$trial" "$lane-next" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        echo "V1017_ERROR_FRONTIER_EXECUTION failed=1 seed=$seed prior_absent=$prior profile=$trial";exit 1;
      }
      test "$(grep -Fxc "V1013_ERROR_CENSUS seed=$seed prior_absent=$prior profile=$trial helper_return=1 shared_time=0 lane=0 ordinal=0 kind=0 depth=0 entries=6 returns=6 msr=2 visits=130 token_preserved=1 saved_fields=38 boundary_executed=0 continuous_boot=0" "$work/run.log")" = 1
      pattern="V1017_ERROR_FRONTIER seed=$seed prior_absent=$prior profile=$trial lane=[1-5] ordinal=[0-9]{1,2} kind=[1-6] handler_time=[01] callback_candidate=[01] transfer_type=[01] visits=[1-9][0-9]{0,3} token_preserved=1 saved_fields=38 call_executed=0"
      test "$(grep -Exc "$pattern" "$work/run.log")" = 1
      grep -Ex "$pattern" "$work/run.log"
    done
  done
  echo "V1017_OWNER_ERROR_FRONTIER mode=$mode classified=16 fallback=0 continuous_boot=0"
  echo "V992_OWNER_SUCCESS_FRONTIER mode=$mode classified=8 fallback=0 continuous_boot=0"
  echo "V988_OWNER_SHARED mode=$mode valid=8 baseline=8 fallback=0 continuous_boot=0"
done
