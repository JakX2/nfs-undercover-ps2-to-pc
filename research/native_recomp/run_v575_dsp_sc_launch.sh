#!/usr/bin/env bash
# Bounded, original DOL-only, headless startup through the DSP flush return.
set -euo pipefail
umask 077
describe=0
if [[ $# == 2 && "$1" == --describe-mode ]]; then
  describe=1
  set -- unused unused unused "$2"
fi
[[ $# == 3 || ( $# == 4 && ( "$4" == dsp-return || "$4" == mi-return || "$4" == report-return || "$4" == arena-return || "$4" == irq-enable-return || "$4" == ipc-client-return || "$4" == stm-open || "$4" == open-request || "$4" == irq-pending-entry || "$4" == irq-si-dispatch || "$4" == irq-si-ack || "$4" == irq-si-postack || "$4" == irq-si-os-leaves || "$4" == irq-si-handler-return || "$4" == irq-si-handler-restore || "$4" == irq-si-handler-time || "$4" == irq-si-time-suffix || "$4" == irq-pending-capture || "$4" == irq-si-combined || "$4" == irq-si-captured || "$4" == irq-si-epilogue || "$4" == irq-si-transfer-prefix || "$4" == irq-si-transfer-return || "$4" == irq-si-transfer-suffix || "$4" == irq-si-alarm || "$4" == irq-si-alarm-suffix || "$4" == irq-si-callback-prefix || "$4" == irq-si-callback-time || "$4" == irq-si-callback-frontier || "$4" == irq-si-wireless-wrapper || "$4" == irq-si-callback-return || "$4" == irq-si-wireless-write || "$4" == irq-si-combined-callback || "$4" == irq-si-handler-suffix ) ) ]] || exit 2
mode="${4:-dsp-sc}"
requested_mode="$mode"
open_request=0
external_entry=0
external_capture=0
if [[ "$mode" == irq-pending-capture ]]; then mode=irq-pending-entry;external_capture=1;fi
si_dispatch=0
si_ack=0
si_postack=0
si_os_leaves=0
si_handler_return=0
si_handler_restore=0
si_handler_time=0
si_time_suffix=0
si_combined=0
si_captured=0
si_epilogue=0
si_transfer_prefix=0
si_transfer_return=0
si_transfer_suffix=0
si_alarm=0
si_alarm_suffix=0
si_callback_prefix=0
si_callback_time=0
si_callback_frontier=0
si_wireless_wrapper=0
si_callback_return=0
si_wireless_write=0
si_combined_callback=0
si_handler_suffix=0
if [[ "$mode" == irq-si-handler-suffix ]]; then mode=irq-si-combined-callback;si_handler_suffix=1;fi
if [[ "$mode" == irq-si-combined-callback ]]; then mode=irq-si-wireless-write;si_combined_callback=1;si_callback_return=1;fi
if [[ "$mode" == irq-si-wireless-write ]]; then mode=irq-si-wireless-wrapper;si_wireless_write=1;fi
if [[ "$mode" == irq-si-callback-return ]]; then mode=irq-si-wireless-wrapper;si_callback_return=1;fi
if [[ "$mode" == irq-si-wireless-wrapper ]]; then mode=irq-si-callback-frontier;si_wireless_wrapper=1;fi
if [[ "$mode" == irq-si-callback-frontier ]]; then mode=irq-si-callback-time;si_callback_frontier=1;fi
if [[ "$mode" == irq-si-callback-time ]]; then mode=irq-si-callback-prefix;si_callback_time=1;fi
if [[ "$mode" == irq-si-callback-prefix ]]; then mode=irq-si-alarm-suffix;si_callback_prefix=1;fi
if [[ "$mode" == irq-si-alarm-suffix ]]; then mode=irq-si-alarm;si_alarm_suffix=1;fi
if [[ "$mode" == irq-si-alarm ]]; then mode=irq-si-transfer-suffix;si_alarm=1;fi
if [[ "$mode" == irq-si-transfer-suffix ]]; then mode=irq-si-transfer-return;si_transfer_suffix=1;fi
if [[ "$mode" == irq-si-transfer-return ]]; then mode=irq-si-transfer-prefix;si_transfer_return=1;fi
if [[ "$mode" == irq-si-transfer-prefix ]]; then mode=irq-si-time-suffix;si_transfer_prefix=1;fi
if [[ "$mode" == irq-si-epilogue ]]; then mode=irq-si-captured;si_epilogue=1;fi
if [[ "$mode" == irq-si-captured ]]; then mode=irq-si-combined;si_captured=1;external_capture=1;fi
if [[ "$mode" == irq-si-combined ]]; then mode=irq-si-handler-return;si_combined=1;fi
if [[ "$mode" == irq-si-time-suffix ]]; then mode=irq-si-handler-time;si_time_suffix=1;fi
if [[ "$mode" == irq-si-handler-time ]]; then mode=irq-si-handler-return;si_handler_time=1;fi
if [[ "$mode" == irq-si-handler-restore ]]; then mode=irq-si-handler-return;si_handler_restore=1;fi
if [[ "$mode" == irq-si-handler-return ]]; then mode=irq-si-os-leaves;si_handler_return=1;fi
if [[ "$mode" == irq-si-os-leaves ]]; then mode=irq-si-postack;si_os_leaves=1;fi
if [[ "$mode" == irq-si-postack ]]; then mode=irq-si-ack;si_postack=1;fi
if [[ "$mode" == irq-si-ack ]]; then mode=irq-si-dispatch;si_ack=1;fi
if [[ "$mode" == irq-si-dispatch ]]; then mode=irq-pending-entry;si_dispatch=1;fi
if [[ "$mode" == irq-pending-entry ]]; then mode=irq-enable-return;external_entry=1;fi
if [[ "$mode" == open-request ]]; then mode=stm-open;open_request=1;fi
extra=();audit=audit_v575_dsp_sc_frontier.py
if [[ "$mode" == dsp-return || "$mode" == mi-return || "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return || "$mode" == ipc-client-return || "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V581_DSP=1);audit=audit_v581_dsp_return.py;fi
if [[ "$mode" == mi-return || "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return || "$mode" == ipc-client-return || "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V591_MI=1 UNDERCOVER_V612_MAPPING=1);audit=audit_v591_memory_init.py;fi
if [[ "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return || "$mode" == ipc-client-return || "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V603_REPORT=1);audit=audit_v603_boot_report.py;fi
if [[ "$mode" == arena-return || "$mode" == irq-enable-return || "$mode" == ipc-client-return || "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V609_ARENA=1);audit=audit_v609_arena_clear.py;fi
if [[ "$mode" == irq-enable-return || "$mode" == ipc-client-return || "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V616_IRQ=1);audit=audit_v616_irq_enable.py;fi
if [[ "$mode" == ipc-client-return || "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V625_IPC=1);audit=audit_v628_startup_census.py;fi
if [[ "$mode" == stm-open ]]; then extra+=(UNDERCOVER_V629_STM=1);audit=audit_v629_stm_open.py;fi
if [[ "$open_request" == 1 ]]; then extra+=(UNDERCOVER_V641_OPEN=1);audit=audit_v641_open_request.py;fi
if [[ "$external_entry" == 1 ]]; then extra+=(UNDERCOVER_V663_EXTERNAL=1);audit=audit_v663_external_entry.py;fi
if [[ "$external_capture" == 1 ]]; then extra+=(UNDERCOVER_V751_CAPTURE=1);audit=audit_v751_cold_capture.py;fi
if [[ "$si_dispatch" == 1 ]]; then extra+=(UNDERCOVER_V667_SI_DISPATCH=1);audit=audit_v667_si_dispatch.py;fi
if [[ "$si_ack" == 1 ]]; then extra+=(UNDERCOVER_V672_SI_ACK=1);audit=audit_v672_si_ack_route.py;fi
if [[ "$si_postack" == 1 ]]; then extra+=(UNDERCOVER_V699_SI_POSTACK=1);audit=audit_v699_si_postack.py;fi
if [[ "$si_os_leaves" == 1 ]]; then extra+=(UNDERCOVER_V709_OS_LEAVES=1);audit=audit_v709_os_leaves.py;fi
if [[ "$si_handler_return" == 1 ]]; then extra+=(UNDERCOVER_V726_HANDLER_RETURN=1);audit=audit_v726_handler_return.py;fi
if [[ "$si_handler_restore" == 1 ]]; then extra+=(UNDERCOVER_V738_RESTORE=1);audit=audit_v738_handler_restore.py;fi
if [[ "$si_handler_time" == 1 ]]; then extra+=(UNDERCOVER_V742_HANDLER_TIME=1);audit=audit_v742_handler_time.py;fi
if [[ "$si_time_suffix" == 1 ]]; then extra+=(UNDERCOVER_V747_TIME_SUFFIX=1);audit=audit_v747_time_suffix.py;fi
if [[ "$si_combined" == 1 ]]; then extra+=(UNDERCOVER_V738_RESTORE=1 UNDERCOVER_V742_HANDLER_TIME=1 UNDERCOVER_V747_TIME_SUFFIX=1);audit=audit_v760_combined_handler.py;fi
if [[ "$si_captured" == 1 ]]; then audit=audit_v761_captured_handler.py;fi
if [[ "$si_epilogue" == 1 ]]; then extra+=(UNDERCOVER_V767_EPILOGUE=1);audit=audit_v767_live_epilogue.py;fi
if [[ "$si_transfer_prefix" == 1 ]]; then extra+=(UNDERCOVER_V768_TRANSFER_PREFIX=1);audit=audit_v768_transfer_prefix.py;fi
if [[ "$si_transfer_return" == 1 ]]; then extra+=(UNDERCOVER_V777_TRANSFER_RETURN=1);audit=audit_v777_transfer_return.py;fi
if [[ "$si_transfer_suffix" == 1 ]]; then extra+=(UNDERCOVER_V778_TRANSFER_SUFFIX=1);audit=audit_v778_transfer_suffix.py;fi
if [[ "$si_alarm" == 1 ]]; then extra+=(UNDERCOVER_V786_ALARM_RETURN=1);audit=audit_v786_alarm_return.py;fi
if [[ "$si_alarm_suffix" == 1 ]]; then extra+=(UNDERCOVER_V789_ALARM_SUFFIX=1);audit=audit_v789_alarm_suffix.py;fi
if [[ "$si_callback_prefix" == 1 ]]; then extra+=(UNDERCOVER_V807_CALLBACK_PREFIX=1);audit=audit_v809_callback_prefix.py;fi
if [[ "$si_callback_time" == 1 ]]; then extra+=(UNDERCOVER_V813_CALLBACK_TIME=1);audit=audit_v822_callback_time.py;fi
if [[ "$si_callback_frontier" == 1 ]]; then extra+=(UNDERCOVER_V831_CALLBACK_FRONTIER=1);audit=audit_v836_callback_frontier.py;fi
if [[ "$si_wireless_wrapper" == 1 ]]; then extra+=(UNDERCOVER_V847_WIRELESS=1);audit=audit_v848_wireless_wrapper.py;fi
if [[ "$si_wireless_write" == 1 ]]; then extra+=(UNDERCOVER_V861_WIRELESS_WRITE=1);audit=audit_v862_wireless_write.py;fi
if [[ "$si_callback_return" == 1 ]]; then extra+=(UNDERCOVER_V850_CALLBACK_RETURN=1);audit=audit_v852_callback_return.py;fi
if [[ "$si_combined_callback" == 1 ]]; then audit=audit_v864_combined_callback.py;fi
if [[ "$si_handler_suffix" == 1 ]]; then extra+=(UNDERCOVER_V868_HANDLER_SUFFIX=1);audit=audit_v870_handler_suffix.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V919_HANDLER_EPILOGUE:-0}" == 1 ]]; then extra+=(UNDERCOVER_V919_HANDLER_EPILOGUE=1);audit=audit_v919_handler_epilogue.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V920_HANDLER_RETURN:-0}" == 1 ]]; then [[ "${UNDERCOVER_RUN_V919_HANDLER_EPILOGUE:-0}" == 1 ]] || exit 2;extra+=(UNDERCOVER_V920_HANDLER_RETURN=1);audit=audit_v920_handler_return.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V921_CAPTURE_JOIN:-0}" == 1 ]]; then [[ "${UNDERCOVER_RUN_V920_HANDLER_RETURN:-0}" == 1 ]] || exit 2;extra+=(UNDERCOVER_V751_CAPTURE=1);audit=audit_v921_capture_join.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V922_IRQ_RETURN:-0}" == 1 ]]; then [[ "${UNDERCOVER_RUN_V921_CAPTURE_JOIN:-0}" == 1 ]] || exit 2;audit=audit_v922_irq_return.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V928_LEAF_FINISH:-0}" == 1 ]]; then [[ "${UNDERCOVER_RUN_V922_IRQ_RETURN:-0}" == 1 ]] || exit 2;audit=audit_v928_leaf_finish.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V930_IPC_JOIN:-0}" == 1 ]]; then [[ "${UNDERCOVER_RUN_V928_LEAF_FINISH:-0}" == 1 ]] || exit 2;audit=audit_v930_ipc_join.py;fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V932_PENDING_RFI:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V922_IRQ_RETURN:-0}" == 1 && "${UNDERCOVER_RUN_V928_LEAF_FINISH:-0}" != 1 && "${UNDERCOVER_RUN_V930_IPC_JOIN:-0}" != 1 ]] || exit 2
  extra+=(UNDERCOVER_V932_PENDING_RFI=1);audit=audit_v932_pending_rfi.py
fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V939_SECOND_VECTOR:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V932_PENDING_RFI:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V939_SECOND_VECTOR=1);audit=audit_v939_second_vector.py
fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V951_SECOND_DISPATCH:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V939_SECOND_VECTOR:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V951_SECOND_DISPATCH=1);audit=audit_v951_second_dispatch.py
fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V958_SECOND_ACK:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V951_SECOND_DISPATCH:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V958_SECOND_ACK=1);audit=audit_v958_second_ack.py
fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V967_POST_ACK:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V958_SECOND_ACK:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V967_POST_ACK=1);audit=audit_v967_post_ack.py
fi
if [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V975_SECOND_TIME:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V967_POST_ACK:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V975_SECOND_TIME=1);audit=audit_v975_second_time.py
fi
if [[ "${UNDERCOVER_RUN_V981_SECOND_FRONTIER:-0}" == 1 ]]; then
  [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V975_SECOND_TIME:-0}" == 1 && "${UNDERCOVER_RUN_V967_POST_ACK:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V981_SECOND_FRONTIER=1);audit=audit_v986_transfer_frontier.py
fi
if [[ "${UNDERCOVER_RUN_V995_SUCCESS_FRONTIER:-0}" == 1 ]]; then
  [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V989_SHARED_COMPLETION:-0}" == 1 && "${UNDERCOVER_RUN_V975_SECOND_TIME:-0}" == 1 && "${UNDERCOVER_RUN_V981_SECOND_FRONTIER:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V989_SHARED_COMPLETION=1 UNDERCOVER_V995_SUCCESS_FRONTIER=1);audit=audit_v995_success_frontier.py
  if [[ "${UNDERCOVER_RUN_V1009_SECOND_CALLBACK:-0}" == 1 ]]; then extra+=(UNDERCOVER_V1009_SECOND_CALLBACK=1);audit=audit_v1009_second_callback.py;fi
elif [[ "${UNDERCOVER_RUN_V989_SHARED_COMPLETION:-0}" == 1 ]]; then
  [[ "$si_handler_suffix" == 1 && "${UNDERCOVER_RUN_V967_POST_ACK:-0}" == 1 && "${UNDERCOVER_RUN_V958_SECOND_ACK:-0}" == 1 && "${UNDERCOVER_RUN_V975_SECOND_TIME:-0}" != 1 && "${UNDERCOVER_RUN_V981_SECOND_FRONTIER:-0}" != 1 ]] || exit 2
  extra+=(UNDERCOVER_V989_SHARED_COMPLETION=1);audit=audit_v989_shared_time.py
fi
if [[ "${UNDERCOVER_RUN_V1014_SECOND_CALLBACK_TIME:-0}" == 1 ]]; then
  [[ "$audit" == audit_v1009_second_callback.py ]] || exit 2
  extra+=(UNDERCOVER_V1014_SECOND_CALLBACK_TIME=1);audit=audit_v1014_second_callback_time.py
fi
if [[ "${UNDERCOVER_RUN_V1021_ERROR_FRONTIER:-0}" == 1 ]]; then
  [[ "${UNDERCOVER_RUN_V1015_ERROR_COMPLETION:-0}" == 1 ]] || exit 2
  case "$audit" in
    audit_v995_success_frontier.py) audit=audit_v1021_error_frontier.py;;
    audit_v1014_second_callback_time.py) audit=audit_v1023_error_callback_time.py;;
    *) exit 2;;
  esac
  extra+=(UNDERCOVER_V1015_ERROR_COMPLETION=1 UNDERCOVER_V1021_ERROR_FRONTIER=1)
  if [[ "${UNDERCOVER_RUN_V1034_QUEUE_DETAIL:-0}" == 1 ]]; then extra+=(UNDERCOVER_V1034_QUEUE_DETAIL=1);fi
elif [[ "${UNDERCOVER_RUN_V1015_ERROR_COMPLETION:-0}" == 1 ]]; then
  [[ "$audit" == audit_v989_shared_time.py ]] || exit 2
  extra+=(UNDERCOVER_V1015_ERROR_COMPLETION=1);audit=audit_v1015_error_completion.py
fi
if [[ "${UNDERCOVER_RUN_V1040_SIX_ARGS:-0}" == 1 ]]; then
  [[ "$audit" == audit_v1021_error_frontier.py && "${UNDERCOVER_RUN_V1034_QUEUE_DETAIL:-0}" == 1 ]] || exit 2
  extra+=(UNDERCOVER_V1040_SIX_ARGS=1);audit=audit_v1041_transfer_abi.py
fi
# The third-transfer continuation has its own strict terminal audit.
# This explicit experiment never changes the cold SI profile.
third="${UNDERCOVER_RUN_V1051_THIRD_TRANSFER:-0}"
third_alarm="${UNDERCOVER_RUN_V1055_THIRD_ALARM:-0}"
[[ "$third" == 0 || "$third" == 1 ]] || exit 2
[[ "$third_alarm" == 0 || "$third_alarm" == 1 ]] || exit 2
[[ "$third_alarm" == 0 || "$third" == 1 ]] || exit 2
third_postalarm="${UNDERCOVER_RUN_V1102_AFTER_ALARM-0}"
[[ "$third_postalarm" == 0 || "$third_postalarm" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1097_AFTER_ALARM-0}" == "$third_postalarm" ]] || exit 2
[[ "$third_postalarm" == 0 || ( "$third_alarm" == 1 && "$third" == 1 && "${UNDERCOVER_RUN_V1018_SECOND_IRQ_MATRIX:-0}" == 0 ) ]] || exit 2
third_postalarm_time="${UNDERCOVER_RUN_V1107_POSTALARM_TIME-0}"
[[ "$third_postalarm_time" == 0 || "$third_postalarm_time" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1106_POSTALARM_TIME-0}" == "$third_postalarm_time" ]] || exit 2
[[ "$third_postalarm_time" == 0 || "$third_postalarm" == 1 ]] || exit 2
third_postalarm_frontier="${UNDERCOVER_RUN_V1114_POSTALARM_FRONTIER-0}"
[[ "$third_postalarm_frontier" == 0 || "$third_postalarm_frontier" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1113_POSTALARM_FRONTIER-0}" == "$third_postalarm_frontier" ]] || exit 2
[[ "$third_postalarm_frontier" == 0 || "$third_postalarm_time" == 1 ]] || exit 2
third_postalarm_wireless="${UNDERCOVER_RUN_V1121_POSTALARM_WIRELESS-0}"
[[ "$third_postalarm_wireless" == 0 || "$third_postalarm_wireless" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1119_POSTALARM_WIRELESS-0}" == "$third_postalarm_wireless" ]] || exit 2
[[ "$third_postalarm_wireless" == 0 || "$third_postalarm_frontier" == 1 ]] || exit 2
third_postalarm_suffix="${UNDERCOVER_RUN_V1127_POSTALARM_SUFFIX-0}"
[[ "$third_postalarm_suffix" == 0 || "$third_postalarm_suffix" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1124_POSTALARM_SUFFIX-0}" == "$third_postalarm_suffix" ]] || exit 2
[[ "$third_postalarm_suffix" == 0 || "$third_postalarm_wireless" == 1 ]] || exit 2
third_postalarm_return="${UNDERCOVER_RUN_V1135_POSTALARM_RETURN-0}"
[[ "$third_postalarm_return" == 0 || "$third_postalarm_return" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1134_POSTALARM_RETURN-0}" == "$third_postalarm_return" ]] || exit 2
[[ "$third_postalarm_return" == 0 || "$third_postalarm_suffix" == 1 ]] || exit 2
third_postalarm_handler="${UNDERCOVER_RUN_V1143_POSTALARM_HANDLER-0}"
[[ "$third_postalarm_handler" == 0 || "$third_postalarm_handler" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1141_POSTALARM_HANDLER-0}" == "$third_postalarm_handler" ]] || exit 2
[[ "$third_postalarm_handler" == 0 || "$third_postalarm_return" == 1 ]] || exit 2
third_postalarm_handler_return="${UNDERCOVER_RUN_V1148_POSTALARM_HANDLER_RETURN-0}"
[[ "$third_postalarm_handler_return" == 0 || "$third_postalarm_handler_return" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1146_POSTALARM_HANDLER_RETURN-0}" == "$third_postalarm_handler_return" ]] || exit 2
[[ "$third_postalarm_handler_return" == 0 || "$third_postalarm_handler" == 1 ]] || exit 2
held_epilogue="${UNDERCOVER_RUN_V1156_HELD_EPILOGUE-0}"
[[ "$held_epilogue" == 0 || "$held_epilogue" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1152_HELD_EPILOGUE-0}" == "$held_epilogue" ]] || exit 2
[[ "$held_epilogue" == 0 || "$third_postalarm_handler_return" == 1 ]] || exit 2
held_dispatch="${UNDERCOVER_RUN_V1163_HELD_DISPATCH-0}"
[[ "$held_dispatch" == 0 || "$held_dispatch" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1161_HELD_DISPATCH-0}" == "$held_dispatch" ]] || exit 2
[[ "$held_dispatch" == 0 || "$held_epilogue" == 1 ]] || exit 2
third_ack="${UNDERCOVER_RUN_V1171_THIRD_ACK-0}"
[[ "$third_ack" == 0 || "$third_ack" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1169_THIRD_ACK-0}" == "$third_ack" ]] || exit 2
[[ "$third_ack" == 0 || "$held_dispatch" == 1 ]] || exit 2
ack_helper="${UNDERCOVER_RUN_V1177_ACK_HELPER-0}"
[[ "$ack_helper" == 0 || "$ack_helper" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1176_ACK_HELPER-0}" == "$ack_helper" ]] || exit 2
[[ "$ack_helper" == 0 || "$third_ack" == 1 ]] || exit 2
ack_callback="${UNDERCOVER_RUN_V1182_ACK_CALLBACK-0}"
[[ "$ack_callback" == 0 || "$ack_callback" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1182_ACK_CALLBACK-0}" == "$ack_callback" ]] || exit 2
[[ "$ack_callback" == 0 || "$ack_helper" == 1 ]] || exit 2
ack_prefix="${UNDERCOVER_RUN_V1187_ACK_PREFIX-0}"
[[ "$ack_prefix" == 0 || "$ack_prefix" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1186_ACK_PREFIX-0}" == "$ack_prefix" ]] || exit 2
[[ "$ack_prefix" == 0 || "$ack_callback" == 1 ]] || exit 2
ack_time="${UNDERCOVER_RUN_V1191_ACK_TIME-0}"
[[ "$ack_time" == 0 || "$ack_time" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1190_ACK_TIME-0}" == "$ack_time" ]] || exit 2
[[ "$ack_time" == 0 || "$ack_prefix" == 1 ]] || exit 2
ack_frontier="${UNDERCOVER_RUN_V1194_ACK_FRONTIER-0}"
[[ "$ack_frontier" == 0 || "$ack_frontier" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1194_ACK_FRONTIER-0}" == "$ack_frontier" ]] || exit 2
[[ "$ack_frontier" == 0 || "$ack_time" == 1 ]] || exit 2
ack_wireless="${UNDERCOVER_RUN_V1198_ACK_WIRELESS-0}"
[[ "$ack_wireless" == 0 || "$ack_wireless" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1198_ACK_WIRELESS-0}" == "$ack_wireless" ]] || exit 2
[[ "$ack_wireless" == 0 || "$ack_frontier" == 1 ]] || exit 2
ack_suffix="${UNDERCOVER_RUN_V1203_ACK_SUFFIX-0}"
[[ "$ack_suffix" == 0 || "$ack_suffix" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1203_ACK_SUFFIX-0}" == "$ack_suffix" ]] || exit 2
[[ "$ack_suffix" == 0 || "$ack_wireless" == 1 ]] || exit 2
ack_return="${UNDERCOVER_RUN_V1207_ACK_RETURN-0}"
[[ "$ack_return" == 0 || "$ack_return" == 1 ]] || exit 2
[[ "${UNDERCOVER_PREPARE_V1207_ACK_RETURN-0}" == "$ack_return" ]] || exit 2
[[ "$ack_return" == 0 || "$ack_suffix" == 1 ]] || exit 2
if [[ "$third" == 1 ]]; then
  [[ "$requested_mode" == irq-si-handler-suffix && "$audit" == audit_v1041_transfer_abi.py &&
     "${UNDERCOVER_PREPARE_V1029_THIRD_TRANSFER:-0}" == 1 &&
     "${UNDERCOVER_PREPARE_V1048_THIRD_ALARM:-0}" == "$third_alarm" ]] || exit 2
  extra+=(UNDERCOVER_V1028_THIRD_TRANSFER=1);audit=audit_v1045_third_transfer_abi.py
  if [[ "$third_alarm" == 1 ]]; then
    extra+=(UNDERCOVER_V1048_THIRD_ALARM=1);audit=audit_v1054_third_alarm.py
    if [[ "$third_postalarm" == 1 ]]; then
      extra+=(UNDERCOVER_V1095_AFTER_ALARM=1);audit=audit_v1101_postalarm.py
      if [[ "$third_postalarm_time" == 1 ]]; then
        extra+=(UNDERCOVER_V1103_POSTALARM_TIME=1);audit=audit_v1107_postalarm_time.py
        if [[ "$third_postalarm_frontier" == 1 ]]; then
          extra+=(UNDERCOVER_V1111_POSTALARM_FRONTIER=1);audit=audit_v1114_postalarm_frontier.py
          if [[ "$third_postalarm_wireless" == 1 ]]; then
            extra+=(UNDERCOVER_V1118_POSTALARM_WIRELESS=1);audit=audit_v1121_postalarm_wireless.py
            if [[ "$third_postalarm_suffix" == 1 ]]; then
              extra+=(UNDERCOVER_V1123_POSTALARM_SUFFIX=1);audit=audit_v1127_postalarm_suffix.py
              if [[ "$third_postalarm_return" == 1 ]]; then
                extra+=(UNDERCOVER_V1132_POSTALARM_RETURN=1);audit=audit_v1135_postalarm_return.py
                if [[ "$third_postalarm_handler" == 1 ]]; then
                  extra+=(UNDERCOVER_V1139_POSTALARM_HANDLER=1);audit=audit_v1143_postalarm_handler.py
                  if [[ "$third_postalarm_handler_return" == 1 ]]; then
                    extra+=(UNDERCOVER_V1145_POSTALARM_HANDLER_RETURN=1);audit=audit_v1148_postalarm_handler_return.py
                    if [[ "$held_epilogue" == 1 ]]; then
                      extra+=(UNDERCOVER_V1151_HELD_EPILOGUE=1);audit=audit_v1156_held_epilogue.py
                      if [[ "$held_dispatch" == 1 ]]; then
                        extra+=(UNDERCOVER_V1158_HELD_DISPATCH=1);audit=audit_v1163_held_dispatch.py
                        if [[ "$third_ack" == 1 ]]; then
                          extra+=(UNDERCOVER_V1167_THIRD_ACK=1);audit=audit_v1171_third_ack.py
                          if [[ "$ack_helper" == 1 ]]; then
                            extra+=(UNDERCOVER_V1175_ACK_HELPER=1);audit=audit_v1177_ack_helper.py
                            if [[ "$ack_callback" == 1 ]]; then
                              extra+=(UNDERCOVER_V1180_ACK_CALLBACK=1);audit=audit_v1182_ack_callback.py
                              if [[ "$ack_prefix" == 1 ]]; then
                                extra+=(UNDERCOVER_V1184_ACK_PREFIX=1);audit=audit_v1187_ack_prefix.py
                                if [[ "$ack_time" == 1 ]]; then
                                  extra+=(UNDERCOVER_V1189_ACK_TIME=1);audit=audit_v1191_ack_time.py
                                  if [[ "$ack_frontier" == 1 ]]; then
                                    extra+=(UNDERCOVER_V1193_ACK_FRONTIER=1);audit=audit_v1194_ack_frontier.py
                                    if [[ "$ack_wireless" == 1 ]]; then
                                      extra+=(UNDERCOVER_V1197_ACK_WIRELESS=1);audit=audit_v1198_ack_wireless.py
                                      if [[ "$ack_suffix" == 1 ]]; then
                                        extra+=(UNDERCOVER_V1201_ACK_SUFFIX=1);audit=audit_v1203_ack_suffix.py
                                        if [[ "$ack_return" == 1 ]]; then
                                          extra+=(UNDERCOVER_V1205_ACK_RETURN=1);audit=audit_v1207_ack_return.py
                                        fi
                                      fi
                                    fi
                                  fi
                                fi
                              fi
                            fi
                          fi
                        fi
                      fi
                    fi
                  fi
                fi
              fi
            fi
          fi
        fi
      fi
    fi
  fi
fi
# Only the second-callback experiment may change the fixed cold SI profile.
# Port zero must remain absent for the verified first completion.
si_profile="${UNDERCOVER_RUN_V1012_SI_PROFILE-absent}"
case "$si_profile" in
  absent) ;;
  port1-present)
    [[ "$requested_mode" == irq-si-handler-suffix && ( "$audit" == audit_v1009_second_callback.py || "$audit" == audit_v1014_second_callback_time.py ) ]] || exit 2
    ;;
  *) exit 2 ;;
esac
# The unchanged wireless setter experiment needs an explicit zero-ID
# cold SRAM fixture, unlike the general nonzero SRAM coverage profile.
sram_profile=pattern
if [[ "$third_postalarm_wireless" == 1 ]]; then sram_profile=wireless-zero;fi
echo "V875_LAUNCH_PLAN requested=$requested_mode base=$mode audit=$audit flags=${extra[*]}"
if [[ "$sram_profile" == wireless-zero ]]; then
  echo 'V1196_SRAM_PLAN selected=wireless-zero unchanged_setter=1 synthetic=1'
fi
if [[ "$si_profile" != absent ]]; then
  echo "V1012_SI_PROFILE selected=port1-present cold_port0_absent=1 synthetic=1"
fi
if [[ "$describe" == 1 ]]; then exit 0;fi
exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$exe" && -x "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
mkdir -m 700 "$work"
printf '%s\n' '[system]' 'platform = "Wii"' '[input]' 'mode = 6' > "$work/config.toml"
python3 "$here/write_sram_profile_v536.py" "$work/exi-test-profile.txt" --profile "$sram_profile"
python3 "$here/write_si_profile_v1012.py" "$si_profile" "$work/si-test-profile.txt"
echo 'V575_DSP_SC_INPUT accepted=1 dol_only=1 profiles=synthetic'
rc=0
(
  cd "$work"
  ulimit -c 0
  ulimit -f 8192
  timeout --signal=TERM --kill-after=3s 20s env -i PATH="$PATH" HOME="$work" \
    NWII_HEADLESS=1 NWII_TRACE_CALLS=1 UNDERCOVER_V419_START=1 \
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \
    UNDERCOVER_V475_IRQ_MMIO=1 UNDERCOVER_V481_IRQ_BANKS=1 UNDERCOVER_V490_EXI_CONTROLLER=1 \
    "UNDERCOVER_V501_EXI_PROFILE=$work/exi-test-profile.txt" \
    UNDERCOVER_V512_SI=1 "UNDERCOVER_V518_SI_PROFILE=$work/si-test-profile.txt" \
    UNDERCOVER_V522_VICLK=0 UNDERCOVER_V537_ACR=1 UNDERCOVER_V574_SC=1 \
    "${extra[@]}" "$exe" "$dol" "$work/config.toml"
) > "$work/run-private.log" 2>&1 || rc=$?
audit_rc=0
python3 "$here/$audit" "$work/run-private.log" "$rc" || audit_rc=$?
if [[ "$rc" == 116 ]]; then
  PYTHONPATH="$here" python3 - "$work/run-private.log" <<'PY'
import sys
from pathlib import Path
from report_diagnostic_v643 import diagnostic,MAX_LOG
p=Path(sys.argv[1])
if p.stat().st_size<=MAX_LOG:
    row=diagnostic(p.read_bytes(),116)
    if row:print(row)
PY
fi
if [[ "$rc" == 119 ]]; then
  PYTHONPATH="$here" python3 - "$work/run-private.log" <<'PY'
import sys
from pathlib import Path
from irq_diagnostic_v661 import diagnostic,MAX_LOG
p=Path(sys.argv[1])
if p.stat().st_size<=MAX_LOG:
    row=diagnostic(p.read_bytes(),119)
    if row:print(row)
PY
fi
# The longer chained audits deliberately emit only their own census. Export
# the same bounded mapper diagnostic if an upstream MI refusal stopped them.
if [[ "$rc" == 115 && "$audit" != audit_v591_memory_init.py ]]; then
  PYTHONPATH="$here" python3 - "$work/run-private.log" <<'PY'
import sys
from pathlib import Path
from audit_v591_memory_init import MAX_LOG,mapper_diagnostic
p=Path(sys.argv[1])
if p.stat().st_size<=MAX_LOG:
    row=mapper_diagnostic(p.read_bytes(),115)
    if row:print(row)
PY
fi
if [[ "$mode" == mi-return || "$mode" == report-return || "$mode" == arena-return || "$mode" == irq-enable-return || "$mode" == ipc-client-return || "$mode" == stm-open ]]; then
  if [[ "$(grep -Fxc 'V612_MAPPING_PROFILE accepted=1 mem1=24 mem2=64 mapped_mem2=52 ipc_kib=512 synthetic=1' "$work/run-private.log" || true)" != 1 ]]; then echo "V612_MAPPING_LAUNCH verified=0";exit 1;fi
  echo "V612_MAPPING_LAUNCH verified=1"
fi
exit "$audit_rc"
