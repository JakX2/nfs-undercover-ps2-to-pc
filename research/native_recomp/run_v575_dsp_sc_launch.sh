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
echo "V875_LAUNCH_PLAN requested=$requested_mode base=$mode audit=$audit flags=${extra[*]}"
if [[ "$describe" == 1 ]]; then exit 0;fi
exe="$(realpath "$1")";dol="$(realpath "$2")";work="$(realpath -m "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ -f "$exe" && -x "$exe" && -f "$dol" && ! -e "$work" && ! -L "$work" ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]] || { echo 'V575_DSP_SC_INPUT accepted=0';exit 1; }
mkdir -m 700 "$work"
printf '%s\n' '[system]' 'platform = "Wii"' '[input]' 'mode = 6' > "$work/config.toml"
python3 "$here/write_sram_profile_v536.py" "$work/exi-test-profile.txt"
printf '%s\n' UNDERCOVER_SI_PROFILE_V1 latency=00000008 port0=absent port1=absent port2=absent port3=absent > "$work/si-test-profile.txt"
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
