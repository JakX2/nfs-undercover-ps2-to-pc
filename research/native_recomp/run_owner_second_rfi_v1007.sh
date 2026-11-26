#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_second_rfi_v1007.py" "$dol" "$elf" "$work/owner_second_dispatch.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26 apply_native_lowmem_v63 apply_exception_sprg; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V955_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_second_rfi_v1007.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$here" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_second_rfi_v1007.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "generate_owner_second_rfi_v1007.cpp";echo "V955_BUILD translator=0";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V955_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_second_rfi_v1007.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie "${inc[@]}" "$here/test_owner_second_rfi_v1007.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_build_v910.py" "$work/build.log" "test_owner_second_rfi_v1007.cpp";echo "V955_BUILD native=0";exit 1; }
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
  for trial in {0..3}; do
    for lane in active-callback successful-alarm active-callback-time active-callback-frontier wireless-unchanged wireless-changed callback-return handler-frontier handler-return second-rfi; do
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        grep -Ex 'V972_TRANSFER_RETURN original_transfer=1 idle=[01] token=[23] pending=[01] visits=[1-9][0-9]* reads=[0-9]+ writes=[0-9]+ saved_fields=38 handler_instruction_executed=0' "$work/run.log" || true
        grep -Ex 'V1003_CALLBACK_SUFFIX ordinal=[0-9]+ target_class=[0-4] visits=[0-9]+ writes=[0-8] polls=[0-9]+' "$work/run.log" || true
        grep -Ex 'V1007_EPILOGUE_(FAULT reason=[0-9]+ stage=[0-9]+ visits=[0-9]+|ENTRY_REFUSAL mask=[0-9]+)' "$work/run.log" || true
        echo 'V1007_CALLBACK_EXECUTION failed=1';exit 1;
      }
      if [[ "$lane" == callback-return || "$lane" == handler-frontier || "$lane" == handler-return || "$lane" == second-rfi ]]; then
        grep -Ex 'V1003_CALLBACK_SUFFIX ordinal=13 target_class=0 visits=[1-9][0-9]* writes=[0-8] polls=[0-9]+' "$work/run.log"
        grep -Ex 'V1003_CALLBACK_RETURN original_callback=1 original_handler_resume=1 abi=1 visits=12 token_preserved=1 saved_fields=38 handler_instruction_executed=0' "$work/run.log"
        if [[ "$lane" == handler-frontier || "$lane" == handler-return || "$lane" == second-rfi ]]; then
          grep -Ex 'V1004_HANDLER_FRONTIER next=(7|8|12) branch_taken=[01] visits=[1-9][0-9]* stores=[0-8] status_reads=1 status_writes=1 token_preserved=1 saved_fields=38 call_executed=0' "$work/run.log"
        fi
        if [[ "$lane" == handler-return || "$lane" == second-rfi ]]; then
          grep -Ex 'V1006_HANDLER_RETURN original_handler=1 original_dispatcher_resume=1 abi=1 restore_gprs=15 visits=21 token_preserved=1 saved_fields=38 dispatcher_instruction_executed=0' "$work/run.log"
        fi
        if [[ "$lane" == second-rfi ]]; then
          grep -Ex 'V1007_SECOND_RFI original_handler=1 original_dispatcher=1 original_scheduler=1 original_context=1 native_rfi=1 synthetic_resume=1 visits=[1-9][0-9]* token_preserved=1 saved_fields=38 resume_instruction_executed=0 boot_verified=0' "$work/run.log"
        fi
      elif [[ "$lane" == wireless-unchanged ]]; then
        grep -Ex 'V1002_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=[1-9][0-9]* stores=[0-9]+ token_preserved=1 saved_fields=38 continuation_executed=0' "$work/run.log"
      elif [[ "$lane" == wireless-changed ]]; then
        grep -Ex 'V1002_WIRELESS_LOCK original_setter_prefix=1 original_unlock_prefix=1 changed=1 visits=[1-9][0-9]* stores=[0-9]+ token_preserved=1 saved_fields=38 exi_instruction_executed=0' "$work/run.log"
      elif [[ "$lane" == active-callback* ]]; then
        grep -Ex 'V994_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=8 visits=[1-9][0-9]* token_preserved=1 saved_fields=38 continuation_executed=0' "$work/run.log"
        if [[ "$lane" == active-callback-time || "$lane" == active-callback-frontier ]]; then
          grep -Ex 'V998_CALLBACK_TIME_RETURN original_time=1 leaves=3 system_visits=25 leaf_visits=[1-9][0-9]* polls=[1-9][0-9]* reads=[1-9][0-9]* token_preserved=1 saved_fields=38 continuation_executed=0' "$work/run.log"
        fi
        if [[ "$lane" == active-callback-frontier ]]; then
          grep -Ex 'V999_CALLBACK_WIRELESS_FRONTIER ordinal=[35] visits=[1-9][0-9]* writes=[0-3] zero_id=[01] token_preserved=1 saved_fields=38 call_executed=0' "$work/run.log"
        fi
      else
        grep -Ex 'V972_TRANSFER_RETURN original_transfer=1 idle=1 token=3 pending=[01] visits=[1-9][0-9]* reads=[0-9]+ writes=[0-9]+ saved_fields=38 handler_instruction_executed=0' "$work/run.log"
        grep -Ex 'V985_ALARM_RETURN original_return=1 queue=1 lane=[0-4] timer=[01] calls=[0-9]+ visits=[1-9][0-9]* token_held=1 saved_fields=38 handler_instruction_executed=0' "$work/run.log"
      fi
    done
  done
  echo "V1007_OWNER_SECOND_RFI mode=$mode native_rfi=4 handler_return=4 callback_return=4 handler_frontier=4 fallback=0 continuous_boot=0"
  for lane in error-rfi error-rfi-cold; do
    prior=0; [[ "$lane" != error-rfi-cold ]] || prior=1
    for trial in {4..7}; do
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        grep -Ex 'V1020_ERROR_(HELPER_RETURN|CALLBACK_ENTRY) prior_absent=[01] profile=[4-7] (original_return=1 shared_time=0 visits=130|original_indirect=1 visits=71) token_preserved=1 saved_fields=38' "$work/run.log" || true
        grep -Ex 'V1007_EPILOGUE_(FAULT reason=[0-9]+ stage=[0-9]+ visits=[0-9]+|ENTRY_REFUSAL mask=[0-9]+)' "$work/run.log" || true
        echo "V1020_ERROR_RFI failed=1 prior_absent=$prior profile=$trial";exit 1;
      }
      grep -Fx "V1020_ERROR_HELPER_RETURN prior_absent=$prior profile=$trial original_return=1 shared_time=0 visits=130 token_preserved=1 saved_fields=38" "$work/run.log"
      grep -Fx "V1020_ERROR_CALLBACK_ENTRY prior_absent=$prior profile=$trial original_indirect=1 visits=71 token_preserved=1 saved_fields=38" "$work/run.log"
      grep -Ex 'V1003_CALLBACK_RETURN original_callback=1 original_handler_resume=1 abi=1 visits=12 token_preserved=1 saved_fields=38 handler_instruction_executed=0' "$work/run.log"
      grep -Ex 'V1006_HANDLER_RETURN original_handler=1 original_dispatcher_resume=1 abi=1 restore_gprs=15 visits=21 token_preserved=1 saved_fields=38 dispatcher_instruction_executed=0' "$work/run.log"
      grep -Ex 'V1007_SECOND_RFI original_handler=1 original_dispatcher=1 original_scheduler=1 original_context=1 native_rfi=1 synthetic_resume=1 visits=[1-9][0-9]* token_preserved=1 saved_fields=38 resume_instruction_executed=0 boot_verified=0' "$work/run.log"
    done
  done
  echo "V1020_OWNER_ERROR_RFI mode=$mode native_rfi=8 fallback=0 continuous_boot=0"
  for lane in error-queue error-queue-cold error-queue-after-alarm error-queue-cold-after-alarm error-queue-due error-queue-cold-due error-queue-delay error-queue-cold-delay error-queue-due-execute error-queue-cold-due-execute error-queue-callback error-queue-cold-callback error-queue-due-callback error-queue-cold-due-callback \
    error-queue-callback-wireless-same error-queue-cold-callback-wireless-same error-queue-due-callback-wireless-same error-queue-cold-due-callback-wireless-same \
    error-queue-callback-wireless-changed error-queue-cold-callback-wireless-changed error-queue-due-callback-wireless-changed error-queue-cold-due-callback-wireless-changed \
    error-queue-callback-return error-queue-cold-callback-return error-queue-due-callback-return error-queue-cold-due-callback-return \
    error-queue-callback-handler error-queue-cold-callback-handler error-queue-due-callback-handler error-queue-cold-due-callback-handler \
    error-queue-callback-rfi error-queue-cold-callback-rfi error-queue-due-callback-rfi error-queue-cold-due-callback-rfi \
    error-queue-callback-vector error-queue-cold-callback-vector error-queue-due-callback-vector error-queue-cold-due-callback-vector \
    error-queue-cold-due-callback-vector-poison \
    error-queue-callback-dispatch error-queue-cold-callback-dispatch error-queue-due-callback-dispatch error-queue-cold-due-callback-dispatch \
    error-queue-callback-ack error-queue-cold-callback-ack error-queue-due-callback-ack error-queue-cold-due-callback-ack \
    error-queue-callback-ack-post error-queue-cold-callback-ack-post error-queue-due-callback-ack-post error-queue-cold-due-callback-ack-post \
    error-queue-callback-ack-time error-queue-cold-callback-ack-time error-queue-due-callback-ack-time error-queue-cold-due-callback-ack-time \
    error-queue-cold-due-callback-ack-frontier \
    error-queue-callback-ack-callback error-queue-cold-callback-ack-callback error-queue-due-callback-ack-callback error-queue-cold-due-callback-ack-callback \
    error-queue-callback-ack-callback-time error-queue-cold-callback-ack-callback-time error-queue-due-callback-ack-callback-time error-queue-cold-due-callback-ack-callback-time \
    error-queue-callback-ack-callback-frontier error-queue-cold-callback-ack-callback-frontier error-queue-due-callback-ack-callback-frontier error-queue-cold-due-callback-ack-callback-frontier \
    error-queue-callback-ack-callback-wireless error-queue-cold-callback-ack-callback-wireless error-queue-due-callback-ack-callback-wireless error-queue-cold-due-callback-ack-callback-wireless \
    error-queue-callback-ack-callback-suffix error-queue-cold-callback-ack-callback-suffix error-queue-due-callback-ack-callback-suffix error-queue-cold-due-callback-ack-callback-suffix \
    error-queue-callback-ack-callback-return error-queue-cold-callback-ack-callback-return error-queue-due-callback-ack-callback-return error-queue-cold-due-callback-ack-callback-return \
    error-queue-callback-ack-callback-handler error-queue-cold-callback-ack-callback-handler error-queue-due-callback-ack-callback-handler error-queue-cold-due-callback-ack-callback-handler \
    error-queue-callback-ack-handler-return error-queue-cold-callback-ack-handler-return error-queue-due-callback-ack-handler-return error-queue-cold-due-callback-ack-handler-return \
    error-queue-callback-ack-callback-rfi error-queue-cold-callback-ack-callback-rfi error-queue-due-callback-ack-callback-rfi error-queue-cold-due-callback-ack-callback-rfi; do
    prior=0; [[ "$lane" != *cold* ]] || prior=1
    for trial in {4..7}; do
      timeout 20s "$work/probe" "$trial" "$lane" "$dol" > "$work/run.log" 2>&1 || {
        grep -Ex 'V955_ACK_FAULT kind=[0-9]{1,2} line=[0-9]{1,4} trial=[0-7] visits=[0-9]{1,4} ack_stage=[0-5] ack_reason=[0-5] ack_visits=[0-9]{1,4} ack_entries=[0-9]{1,4} stage=[0-6] reason=[0-5] entries=[0-9]{1,2} polls=[0-9]{1,4} reads=[0-9]{1,3}' "$work/run.log" || true
        grep -Ex 'V1022_ERROR_TRANSFER_ENTRY prior_absent=[01] profile=[4-7] original_call=1 visits=78 handler_time=1 token_preserved=1 saved_fields=38' "$work/run.log" || true
        grep -Ex 'V972_TRANSFER_RETURN original_transfer=1 idle=1 token=3 pending=[01] visits=[1-9][0-9]* reads=[0-9]+ writes=[0-9]+ saved_fields=38 handler_instruction_executed=0' "$work/run.log" || true
        grep -Ex 'V1063_THIRD_HANDLER_FRONTIER ordinal=[0-9]{1,2} branch_taken=[01] visits=[0-9]{1,3} stores=[0-8] status_reads=1 status_writes=1 token=3 held=1 saved_fields=38 call_executed=0' "$work/run.log" || true
        grep -Ex 'V1064_THIRD_EPILOGUE_(FAULT reason=[0-9]{1,2} stage=[0-3] visits=[0-9]{1,3}|ENTRY_REFUSAL mask=[0-9]{1,3})' "$work/run.log" || true
        grep -Ex 'V1068_THIRD_GUARD_REFUSAL handler_stage=[0-5] callback_stage=[0-5] dispatcher_owner=[01] dispatcher_resume=[01]' "$work/run.log" || true
        grep -Ex 'V1070_THIRD_VECTOR_REFUSAL stage=([0-9]|1[0-9]|2[0-8]) reason=[0-9]{1,2} vector_reason=[0-6] vector_visits=[0-9]{1,3} trampoline_visits=[0-9]{1,3} poisoned=(0|38)' "$work/run.log" || true
        grep -Ex 'V1086_THIRD_ACK_REFUSAL route=[0-9]{1,2} ack=[0-5] calls=[0-5] ack_stage=[0-5] visits=[0-9]{1,4} helper_return=[01] time_return=[01]' "$work/run.log" || true
        grep -Ex 'V1130_THIRD_EPILOGUE_REFUSAL stage=[0-4] reason=[0-9] entry_mask=[0-9]{1,3}' "$work/run.log" || true
        echo "V1022_ERROR_QUEUE failed=1 prior_absent=$prior profile=$trial";exit 1;
      }
      grep -Fx "V1020_ERROR_HELPER_RETURN prior_absent=$prior profile=$trial original_return=1 shared_time=0 visits=130 token_preserved=1 saved_fields=38" "$work/run.log"
      due=0; [[ "$lane" != *due* ]] || due=1
      delay=0; [[ "$lane" != *delay ]] || delay=1
      if [[ "$due" == 1 || "$delay" == 1 ]]; then
        grep -Ex "V1039_DELAY_FRONTIER delay=$delay prior_absent=$prior profile=$trial branch=[46] handler_time=[01] visits=[1-9][0-9]{0,3} token=2 call_executed=0" "$work/run.log"
        if grep -Eq "^V1039_DELAY_FRONTIER .* branch=4 " "$work/run.log"; then
          grep -Ex "V1037_OWNER_QUEUE_HISTORY delay=$delay due=$due prior_absent=$prior profile=$trial initial_mismatch=[0-9]{1,3} current_mismatch=[0-9]{1,3} changed=[0-9]{1,3} initial_slot_kind=[0-2] samples=[1-9][0-9]{0,3}" "$work/run.log"
          grep -Ex "V1034_OWNER_QUEUE_DETAIL due=$due prior_absent=$prior profile=$trial mismatch_mask=[0-9]{1,3} slot_kind=[0-2] arg_time_zero=[01] queue_time_zero=[01] admitted=[01]" "$work/run.log"
        fi
        if [[ "$lane" != *due-execute && "$lane" != *due-callback* ]]; then continue;fi
        grep -Fx 'V1052_DUE_ADMISSION original_queue=1 admission=2 timing_only=1 unchanged=1 token=2' "$work/run.log"
        grep -Fx 'V1052_DUE_RETURN original_transfer=1 original_alarm=1 token=3 saved_fields=38 boot_verified=0' "$work/run.log"
      fi
      grep -Fx "V1022_ERROR_TRANSFER_ENTRY prior_absent=$prior profile=$trial original_call=1 visits=78 handler_time=1 token_preserved=1 saved_fields=38" "$work/run.log"
      grep -Ex "V1037_OWNER_QUEUE_HISTORY delay=$delay due=$due prior_absent=$prior profile=$trial initial_mismatch=[0-9]{1,3} current_mismatch=[0-9]{1,3} changed=[0-9]{1,3} initial_slot_kind=[0-2] samples=[1-9][0-9]{0,3}" "$work/run.log"
      grep -Ex "V1034_OWNER_QUEUE_DETAIL due=$due prior_absent=$prior profile=$trial mismatch_mask=[0-9]{1,3} slot_kind=[0-2] arg_time_zero=[01] queue_time_zero=[01] admitted=[01]" "$work/run.log"
      grep -Ex 'V972_TRANSFER_RETURN original_transfer=1 idle=1 token=3 pending=[01] visits=[1-9][0-9]* reads=[0-9]+ writes=[0-9]+ saved_fields=38 handler_instruction_executed=0' "$work/run.log"
      grep -Ex 'V985_ALARM_RETURN original_return=1 queue=1 lane=[0-4] timer=[01] calls=[0-9]+ visits=[1-9][0-9]* token_held=1 saved_fields=38 handler_instruction_executed=0' "$work/run.log"
      grep -Fx 'V1032_THIRD_CALL_CENSUS entries=5 returns=5 visits=105 token=3' "$work/run.log"
      grep -Fx 'V1054_THIRD_ALARM_CENSUS suffix_visits=6 status_reads=0 status_writes=0 alarm_lane=0 alarm_visits=33 calls=3 token=3 held=1' "$work/run.log"
      if [[ "$lane" == *after-alarm || "$lane" == *callback* ]]; then
        grep -Ex "V1032_AFTER_ALARM_FRONTIER prior_absent=$prior profile=$trial ordinal=[0-9]+ kind=[0-2] target_class=[0-4] visits=[1-9][0-9]* token=3 held=1 saved_fields=38 call_executed=0" "$work/run.log"
      fi
      if [[ "$lane" == *callback* ]]; then
        grep -Fx 'V1053_THIRD_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=8 visits=13 token=3 held=1 saved_fields=38 continuation_executed=0' "$work/run.log"
        grep -Fx 'V1053_THIRD_CALLBACK_TIME original_time=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 token=3 held=1 saved_fields=38 continuation_executed=0' "$work/run.log"
        grep -Fx 'V1053_THIRD_CALLBACK_FRONTIER ordinal=3 visits=17 writes=3 zero_id=1 token=3 held=1 saved_fields=38 call_executed=0' "$work/run.log"
      fi
      if [[ "$lane" == *wireless-same || "$lane" == *callback-return || "$lane" == *callback-handler || "$lane" == *callback-rfi || "$lane" == *callback-vector* || "$lane" == *callback-dispatch || "$lane" == *callback-ack* ]]; then
        grep -Fx 'V1058_THIRD_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=66 stores=12 token=3 held=1 saved_fields=38 continuation_executed=0' "$work/run.log"
        if [[ "$lane" == *callback-return || "$lane" == *callback-handler || "$lane" == *callback-rfi || "$lane" == *callback-vector* || "$lane" == *callback-dispatch || "$lane" == *callback-ack* ]]; then
          grep -Fx 'V1060_THIRD_CALLBACK_SUFFIX ordinal=13 target_class=0 visits=37 writes=0 polls=4 token=3 held=1 saved_fields=38 call_executed=0' "$work/run.log"
          grep -Fx 'V1060_THIRD_CALLBACK_RETURN original_callback=1 original_handler_resume=1 abi=1 visits=12 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0' "$work/run.log"
        fi
        if [[ "$lane" == *callback-handler || "$lane" == *callback-rfi || "$lane" == *callback-vector* || "$lane" == *callback-dispatch || "$lane" == *callback-ack* ]]; then
          grep -Fx 'V1063_THIRD_HANDLER_FRONTIER ordinal=12 branch_taken=1 visits=20 stores=0 status_reads=1 status_writes=1 token=3 held=1 saved_fields=38 call_executed=0' "$work/run.log"
          grep -Fx 'V1063_THIRD_HANDLER_RETURN original_handler=1 original_dispatcher_resume=1 abi=1 restore_gprs=15 visits=21 token=3 held=1 saved_fields=38 dispatcher_instruction_executed=0 boot_verified=0' "$work/run.log"
        fi
        if [[ "$lane" == *callback-rfi || "$lane" == *callback-vector* || "$lane" == *callback-dispatch || "$lane" == *callback-ack* ]]; then
          grep -Fx 'V1064_THIRD_PENDING_RFI original_handler=1 original_dispatcher=1 original_scheduler=1 original_context=1 native_rfi=1 token=3 held=1 visits=82 saved_fields=38 third_vector_executed=0 resume_instruction_executed=0 boot_verified=0' "$work/run.log"
          if [[ "$lane" == *callback-vector* || "$lane" == *callback-dispatch || "$lane" == *callback-ack* ]]; then
            grep -Fx 'V1069_THIRD_VECTOR original_vector=1 original_trampoline=1 vector_visits=34 trampoline_visits=20 token=3 held=1 saved_fields=38 dispatcher_instruction_executed=0 boot_verified=0' "$work/run.log"
            if [[ "$lane" == *vector-poison ]]; then
              grep -Fx 'V1070_THIRD_VECTOR_FRAME poisoned=38 verified=38 fixture_only=1 original_dispatcher_instruction_executed=0' "$work/run.log"
            else
              grep -Fx 'V1070_THIRD_VECTOR_FRAME poisoned=0 verified=38 fixture_only=0 original_dispatcher_instruction_executed=0' "$work/run.log"
            fi
            if [[ "$lane" == *callback-dispatch || "$lane" == *callback-ack* ]]; then
              grep -Fx 'V1076_THIRD_DISPATCH original_dispatcher=1 original_leaves=4 original_indirect=1 visits=153 entries=5 pi_reads=2 polls=10 token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0' "$work/run.log"
            fi
            if [[ "$lane" == *callback-ack* ]]; then
              grep -Fx 'V1079_THIRD_ACK original_w1c=1 next_label=1 token=3 no_response=1 visits=48 entries=2 returns=1 reads=3 writes=1 saved_fields=38 retired_transfer=1 pi_cleared=1 successor_executed=0 boot_verified=0' "$work/run.log"
              if [[ "$lane" == *ack-post || "$lane" == *ack-time || "$lane" == *ack-frontier || "$lane" == *ack-callback* ]]; then
                grep -Fx 'V1084_THIRD_HELPER_RETURN original_helper=1 visits=130 entries=6 returns=6 msr=2 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0' "$work/run.log"
              fi
              if [[ "$lane" == *ack-time || "$lane" == *ack-frontier || "$lane" == *ack-callback* ]]; then
                if grep -q '^V1088_THIRD_CALLBACK_FRONTIER ' "$work/run.log"; then
                  grep -Ex 'V1088_THIRD_CALLBACK_FRONTIER ordinal=6 target_class=[0-4] visits=71 handler_time=0 token=3 saved_fields=38 pi_cleared=1 original_call_executed=0 boot_verified=0' "$work/run.log"
                  ! grep -Eq '^V1084_THIRD_TIME_RETURN |^V1086_FOURTH_FRONTIER ' "$work/run.log"
                  if [[ "$lane" == *ack-callback* ]]; then
                    grep -Fx 'V1092_THIRD_ACK_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes=8 visits=13 token=3 pi_cleared=1 saved_fields=38 continuation_executed=0 boot_verified=0' "$work/run.log"
                    if [[ "$lane" == *ack-callback-time || "$lane" == *ack-callback-frontier || "$lane" == *ack-callback-wireless || "$lane" == *ack-callback-suffix || "$lane" == *ack-callback-return || "$lane" == *ack-callback-handler || "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                      grep -Fx 'V1105_THIRD_ACK_CALLBACK_TIME original_time=1 leaves=3 system_visits=25 leaf_visits=18 polls=1 reads=3 token=3 pi_cleared=1 saved_fields=38 continuation_executed=0 boot_verified=0' "$work/run.log"
                      if [[ "$lane" == *ack-callback-frontier || "$lane" == *ack-callback-wireless || "$lane" == *ack-callback-suffix || "$lane" == *ack-callback-return || "$lane" == *ack-callback-handler || "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                        grep -Fx 'V1108_THIRD_ACK_WIRELESS_FRONTIER ordinal=3 visits=17 writes=3 zero_id=1 token=3 pi_cleared=1 saved_fields=38 call_executed=0 boot_verified=0' "$work/run.log"
                        if [[ "$lane" == *ack-callback-wireless || "$lane" == *ack-callback-suffix || "$lane" == *ack-callback-return || "$lane" == *ack-callback-handler || "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                          grep -Fx 'V1112_THIRD_ACK_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits=66 stores=12 token=3 pi_cleared=1 saved_fields=38 continuation_executed=0 boot_verified=0' "$work/run.log"
                          if [[ "$lane" == *ack-callback-suffix || "$lane" == *ack-callback-return || "$lane" == *ack-callback-handler || "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                            grep -Fx 'V1115_THIRD_ACK_CALLBACK_SUFFIX ordinal=13 target_class=0 visits=37 writes=0 polls=4 token=3 pi_cleared=1 saved_fields=38 call_executed=0 boot_verified=0' "$work/run.log"
                            if [[ "$lane" == *ack-callback-return || "$lane" == *ack-callback-handler || "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                              grep -Fx 'V1117_THIRD_ACK_CALLBACK_RETURN original_restore=1 original_return=1 visits=12 token=3 pi_cleared=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0' "$work/run.log"
                              if [[ "$lane" == *ack-callback-handler || "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                                grep -Fx 'V1122_THIRD_ACK_HANDLER_FRONTIER ordinal=12 branch_taken=1 visits=20 stores=0 status_reads=1 status_writes=1 token=3 pi_cleared=1 saved_fields=38 call_executed=0 boot_verified=0' "$work/run.log"
                                if [[ "$lane" == *ack-handler-return || "$lane" == *ack-callback-rfi ]]; then
                                  grep -Fx 'V1126_THIRD_ACK_HANDLER_RETURN original_handler=1 original_dispatcher_resume=1 abi=1 restore_gprs=15 visits=21 token=3 pi_cleared=1 saved_fields=38 dispatcher_instruction_executed=0 boot_verified=0' "$work/run.log"
                                  if [[ "$lane" == *ack-callback-rfi ]]; then
                                    grep -Ex 'V1130_THIRD_ACK_RFI original_handler=1 original_dispatcher=1 original_scheduler=1 original_context=1 native_rfi=1 polls=2 visits=[1-9][0-9]{0,2} token=3 pi_cleared=1 saved_fields=38 resume_instruction_executed=0 boot_verified=0' "$work/run.log"
                                  fi
                                fi
                              fi
                            fi
                          fi
                        fi
                      fi
                    fi
                  fi
                else
                  [[ "$lane" != *ack-callback* ]]
                  grep -Fx 'V1084_THIRD_TIME_RETURN original_time=1 leaves=3 visits=44 token=3 saved_fields=38 pi_cleared=1 handler_instruction_executed=0 boot_verified=0' "$work/run.log"
                  if [[ "$lane" == *ack-frontier ]]; then
                    grep -Ex 'V1086_FOURTH_FRONTIER type=[01] idle=[01] callback=[01] channel=[0-3] mismatch=[0-9]{1,3} slot_kind=[0-2] initial_mismatch=[0-9]{1,3} changed=[0-9]{1,3} samples=[1-9][0-9]{0,3} admission=[0-2] visits=[1-9][0-9]{0,3} token=3 saved_fields=38 original_call_executed=0 boot_verified=0' "$work/run.log"
                  fi
                fi
              fi
            fi
          fi
        fi
      elif [[ "$lane" == *wireless-changed ]]; then
        grep -Fx 'V1058_THIRD_WIRELESS_LOCK original_setter_prefix=1 original_unlock_prefix=1 changed=1 visits=69 stores=13 token=3 held=1 saved_fields=38 exi_instruction_executed=0' "$work/run.log"
      fi
    done
  done
  echo "V1022_OWNER_ERROR_QUEUE mode=$mode transfer_return=8 alarm_return=8 fallback=0 continuous_boot=0"
  echo "V1032_OWNER_AFTER_ALARM mode=$mode classified=8 fallback=0 continuous_boot=0"
  echo "V1034_OWNER_QUEUE_DETAIL_CENSUS mode=$mode baseline=16 nonzero_due=8 fallback=0 continuous_boot=0"
  echo "V1037_OWNER_HISTORY mode=$mode baseline=16 discovery_delay=8 fallback=0 continuous_boot=0"
  echo "V1039_OWNER_DELAY_FRONTIERS mode=$mode classified=16 call_executed=0 fallback=0 continuous_boot=0"
  echo "V1052_OWNER_DUE_EXECUTION mode=$mode transfer_return=8 alarm_return=8 fallback=0 continuous_boot=0"
  echo "V1053_OWNER_THIRD_CALLBACK mode=$mode prefix=16 time=16 frontier=16 fallback=0 continuous_boot=0"
  echo "V1058_OWNER_THIRD_WIRELESS mode=$mode unchanged_return=16 changed_lock=16 fallback=0 continuous_boot=0"
  echo "V1060_OWNER_THIRD_CALLBACK_RETURN mode=$mode restored=16 original_handler_resume=16 fallback=0 continuous_boot=0"
  echo "V1063_OWNER_THIRD_HANDLER_RETURN mode=$mode status_w1c=16 original_dispatcher_resume=16 fallback=0 continuous_boot=0"
  echo "V1064_OWNER_THIRD_PENDING_RFI mode=$mode native_rfi=16 held_token=16 third_vector_executed=0 fallback=0 continuous_boot=0"
  echo "V1069_OWNER_THIRD_VECTOR mode=$mode original_vector=16 original_trampoline=16 held_token=16 fallback=0 continuous_boot=0"
  echo "V1070_OWNER_THIRD_VECTOR_FRAME mode=$mode stale_frame_rewritten=4 fields=38 fallback=0 continuous_boot=0"
  echo "V1076_OWNER_THIRD_DISPATCH mode=$mode original_handler_entry=16 pi_reads=32 held_token=16 fallback=0 continuous_boot=0"
  echo "V1079_OWNER_THIRD_ACK mode=$mode original_w1c=16 next_label=16 retired_transfer=16 fallback=0 continuous_boot=0"
  echo "V1088_OWNER_THIRD_POSTACK mode=$mode helper_return=16 classified_branch=20 fallback=0 continuous_boot=0"
  echo "V1092_OWNER_THIRD_ACK_CALLBACK mode=$mode original_prefix=16 save_return=16 fallback=0 continuous_boot=0"
  echo "V1105_OWNER_THIRD_ACK_TIME mode=$mode original_time=16 pi_cleared=16 fallback=0 continuous_boot=0"
  echo "V1108_OWNER_THIRD_ACK_FRONTIER mode=$mode classified=16 original_call_executed=0 fallback=0 continuous_boot=0"
  echo "V1112_OWNER_THIRD_ACK_WIRELESS mode=$mode setter_return=16 unlock_return=16 fallback=0 continuous_boot=0"
  echo "V1115_OWNER_THIRD_ACK_SUFFIX mode=$mode classified=16 call_executed=0 fallback=0 continuous_boot=0"
  echo "V1117_OWNER_THIRD_ACK_RETURN mode=$mode callback_return=16 restored_abi=16 fallback=0 continuous_boot=0"
  echo "V1122_OWNER_THIRD_ACK_HANDLER mode=$mode classified=16 status_read=16 status_w1c=16 fallback=0 continuous_boot=0"
  echo "V1126_OWNER_THIRD_ACK_HANDLER_RETURN mode=$mode handler_return=16 restored_abi=16 fallback=0 continuous_boot=0"
  echo "V1130_OWNER_THIRD_ACK_RFI mode=$mode native_rfi=16 post_rfi_polls=32 fallback=0 continuous_boot=0"
  echo "V992_OWNER_SUCCESS_FRONTIER mode=$mode classified=8 fallback=0 continuous_boot=0"
  echo "V988_OWNER_SHARED mode=$mode valid=8 baseline=8 fallback=0 continuous_boot=0"
done
