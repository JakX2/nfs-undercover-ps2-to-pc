#!/usr/bin/env bash
# Full-image translation and opt-in bounded DSP SC startup; private scratch only.
set -euo pipefail
[[ $# == 3 || ( $# == 4 && ( "$4" == --prepare-dsp-sc || "$4" == --run-dsp-sc || "$4" == --run-dsp-return || "$4" == --prepare-mi || "$4" == --run-mi || "$4" == --prepare-report || "$4" == --prepare-report-observer || "$4" == --run-report || "$4" == --prepare-arena || "$4" == --run-arena || "$4" == --prepare-irq-enable || "$4" == --run-irq-enable || "$4" == --prepare-ipc-client || "$4" == --run-ipc-client || "$4" == --prepare-stm-open || "$4" == --run-stm-open || "$4" == --prepare-open-request || "$4" == --run-open-request || "$4" == --prepare-external-overlay || "$4" == --prepare-external-entry || "$4" == --run-external-entry || "$4" == --prepare-si-dispatch || "$4" == --run-si-dispatch || "$4" == --prepare-si-ack || "$4" == --run-si-ack || "$4" == --run-si-postack || "$4" == --run-si-os-leaves || "$4" == --prepare-si-os-leaves || "$4" == --run-si-handler-return || "$4" == --prepare-si-handler-return || "$4" == --prepare-si-handler-restore || "$4" == --run-si-handler-restore || "$4" == --prepare-si-handler-time || "$4" == --run-si-handler-time || "$4" == --run-si-time-suffix || "$4" == --run-external-capture || "$4" == --prepare-external-capture || "$4" == --prepare-si-combined || "$4" == --run-si-combined || "$4" == --prepare-si-captured || "$4" == --run-si-captured || "$4" == --prepare-si-epilogue || "$4" == --run-si-epilogue || "$4" == --prepare-si-transfer-prefix || "$4" == --run-si-transfer-prefix || "$4" == --prepare-si-transfer-return || "$4" == --run-si-transfer-return || "$4" == --prepare-si-transfer-suffix || "$4" == --run-si-transfer-suffix || "$4" == --prepare-si-alarm || "$4" == --run-si-alarm || "$4" == --prepare-si-alarm-suffix || "$4" == --run-si-alarm-suffix || "$4" == --prepare-si-callback-prefix || "$4" == --run-si-callback-prefix || "$4" == --prepare-si-callback-time || "$4" == --run-si-callback-time || "$4" == --prepare-si-callback-frontier || "$4" == --run-si-callback-frontier || "$4" == --prepare-si-wireless-wrapper || "$4" == --prepare-si-callback-return ) ) ]] || exit 2
mode="${4:-translation-only}"
external_args=()
external_entry=0
external_capture=0
if [[ "$mode" == --run-external-capture ]]; then mode=--run-external-entry;external_capture=1;fi
if [[ "$mode" == --prepare-external-capture ]]; then mode=--prepare-external-entry;external_capture=1;fi
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
if [[ "$mode" == --prepare-si-callback-return ]]; then mode=--prepare-si-wireless-wrapper;si_callback_return=1;fi
if [[ "$mode" == --prepare-si-wireless-wrapper ]]; then mode=--prepare-si-callback-frontier;si_wireless_wrapper=1;fi
if [[ "$mode" == --run-si-callback-frontier ]]; then mode=--run-si-callback-time;si_callback_frontier=1;fi
if [[ "$mode" == --prepare-si-callback-frontier ]]; then mode=--prepare-si-callback-time;si_callback_frontier=1;fi
if [[ "$mode" == --run-si-callback-time ]]; then mode=--run-si-callback-prefix;si_callback_time=1;fi
if [[ "$mode" == --prepare-si-callback-time ]]; then mode=--prepare-si-callback-prefix;si_callback_time=1;fi
if [[ "$mode" == --run-si-callback-prefix ]]; then mode=--run-si-alarm-suffix;si_callback_prefix=1;fi
if [[ "$mode" == --prepare-si-callback-prefix ]]; then mode=--prepare-si-alarm-suffix;si_callback_prefix=1;fi
if [[ "$mode" == --prepare-si-alarm-suffix ]]; then mode=--prepare-si-alarm;si_alarm_suffix=1;fi
if [[ "$mode" == --run-si-alarm-suffix ]]; then mode=--run-si-alarm;si_alarm_suffix=1;fi
if [[ "$mode" == --prepare-si-alarm ]]; then mode=--prepare-si-transfer-suffix;si_alarm=1;fi
if [[ "$mode" == --run-si-alarm ]]; then mode=--run-si-transfer-suffix;si_alarm=1;fi
if [[ "$mode" == --prepare-si-transfer-suffix ]]; then mode=--prepare-si-transfer-return;si_transfer_suffix=1;fi
if [[ "$mode" == --run-si-transfer-suffix ]]; then mode=--run-si-transfer-return;si_transfer_suffix=1;fi
if [[ "$mode" == --prepare-si-transfer-return ]]; then mode=--prepare-si-transfer-prefix;si_transfer_return=1;fi
if [[ "$mode" == --run-si-transfer-return ]]; then mode=--run-si-transfer-prefix;si_transfer_return=1;fi
if [[ "$mode" == --prepare-si-transfer-prefix ]]; then mode=--prepare-si-handler-time;si_transfer_prefix=1;fi
if [[ "$mode" == --run-si-transfer-prefix ]]; then mode=--run-si-time-suffix;si_transfer_prefix=1;fi
if [[ "$mode" == --prepare-si-epilogue ]]; then mode=--prepare-si-captured;si_epilogue=1;fi
if [[ "$mode" == --run-si-epilogue ]]; then mode=--run-si-captured;si_epilogue=1;fi
if [[ "$mode" == --prepare-si-captured ]]; then mode=--prepare-si-combined;si_captured=1;external_capture=1;fi
if [[ "$mode" == --run-si-captured ]]; then mode=--run-si-combined;si_captured=1;external_capture=1;fi
if [[ "$mode" == --prepare-si-combined ]]; then mode=--prepare-si-handler-return;si_combined=1;fi
if [[ "$mode" == --run-si-combined ]]; then mode=--run-si-handler-return;si_combined=1;fi
if [[ "$mode" == --run-si-time-suffix ]]; then mode=--run-si-handler-time;si_time_suffix=1;fi
if [[ "$mode" == --run-si-handler-time ]]; then mode=--run-si-handler-return;si_handler_time=1;fi
if [[ "$mode" == --prepare-si-handler-time ]]; then mode=--prepare-si-handler-return;si_handler_time=1;fi
if [[ "$mode" == --run-si-handler-restore ]]; then mode=--run-si-handler-return;si_handler_restore=1;fi
if [[ "$mode" == --prepare-si-handler-restore ]]; then mode=--prepare-si-handler-return;si_handler_restore=1;fi
if [[ "$mode" == --run-si-handler-return ]]; then mode=--run-si-os-leaves;si_handler_return=1;fi
if [[ "$mode" == --prepare-si-handler-return ]]; then mode=--prepare-si-os-leaves;si_handler_return=1;fi
if [[ "$mode" == --run-si-os-leaves ]]; then mode=--run-si-postack;si_os_leaves=1;fi
if [[ "$mode" == --prepare-si-os-leaves ]]; then mode=--prepare-si-ack;si_os_leaves=1;fi
if [[ "$mode" == --run-si-postack ]]; then mode=--run-si-ack;si_postack=1;fi
if [[ "$mode" == --prepare-si-ack || "$mode" == --run-si-ack ]]; then
  si_ack=1;mode="${mode%-si-ack}-si-dispatch"
fi
if [[ "$mode" == --prepare-si-dispatch || "$mode" == --run-si-dispatch ]]; then
  si_dispatch=1;mode="${mode%-si-dispatch}-external-entry"
fi
if [[ "$mode" == --prepare-external-entry || "$mode" == --run-external-entry ]]; then
  external_entry=1;external_args+=(--native-external-overlay-preflight)
  mode="${mode%-external-entry}-irq-enable"
fi
if [[ "$mode" == --prepare-external-overlay ]]; then
  mode=translation-only;external_args+=(--native-external-overlay-preflight)
fi
open_request=0
if [[ "$mode" == --prepare-open-request ]]; then mode=--prepare-stm-open;open_request=1;fi
if [[ "$mode" == --run-open-request ]]; then mode=--run-stm-open;open_request=1;fi
root="$(realpath "$1")"; dol="$(realpath "$2")"; elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf -- "$work"' EXIT; umask 077
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]]
mkdir "$work/nwii" "$work/generated"
git -C "$root" archive HEAD | tar -x -C "$work/nwii"
nw="$work/nwii"
if [[ "$mode" == --prepare-mi || "$mode" == --run-mi || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/make_v586_bat_roots.py" "$dol" "$elf" "$work/symbols.csv"
else
  python3 "$here/make_private_elf_symbol_map.py" "$elf" "$work/symbols.csv"
fi
for p in apply_psq_indexed_patch apply_psq_estimate_and_gqr_v5 apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_perf_sprs_v29 apply_hid_state_v18 apply_fpscr_v19 apply_l2cr_v20 apply_mtmsr_resume_v74 verify_perf_combo_v29 apply_hid4_continuous_v30 apply_cache_continuous_v39 apply_cache_trace_v44 apply_dcbz_v67 apply_cache_order_v456 apply_data_cache_invalidate_v532 apply_native_lowmem_v63 apply_syscall_pc_v26 apply_syscall_transfer_v461; do
  python3 "$here/$p.py" "$nw" > "$work/patch.log" 2>&1 || { echo "V572 full-image source patch failed: $p";exit 1; }
done
if [[ "$mode" != translation-only && "$mode" != --prepare-mi && "$mode" != --prepare-report ]]; then
  for p in apply_exi_tick_v497 apply_si_tick_v515; do
    python3 "$here/$p.py" "$nw" emitter > "$work/patch.log" 2>&1 || { echo "V574 emitter patch failed: $p";exit 1; }
  done
fi
if [[ "$mode" == --run-dsp-return || "$mode" == --run-mi || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/apply_aram_binding_v553.py" "$nw" emitter > "$work/patch.log" 2>&1 || { echo "V581 ARAM emitter patch failed";exit 1; }
fi
if [[ "$mode" == --prepare-mi || "$mode" == --run-mi || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/apply_bat_roots_v586.py" "$nw"
  python3 "$here/apply_bat_registers_v65.py" "$nw" > "$work/patch.log" 2>&1 || { echo "V584 BAT source patch failed";exit 1; }
  g++ -std=c++20 -O1 -Wall -Wextra -Werror -I"$nw/nWiiRuntime/include" "$here/test_bat_registers_v65.cpp" -o "$work/bat-registers" > "$work/bat-compile.log" 2>&1 || { echo "V584 BAT register test build failed";exit 1; }
  "$work/bat-registers"
fi
if [[ "$mode" == --prepare-report || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/make_v594_boot_report_geometry.py" "$dol" "$elf"
  python3 "$here/apply_report_table_v594.py" "$nw" "$dol" "$elf"
fi
if [[ "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/apply_stm_native_open_v632.py" "$nw" "$dol" "$elf"
  if [[ "$open_request" == 1 ]]; then python3 "$here/apply_open_roots_v645.py" "$nw" "$dol" "$elf";fi
fi
if [[ "$external_entry" == 1 ]]; then
  helper_args=()
  [[ "$si_ack" != 1 ]] || helper_args+=(--first-ack-helper)
  if [[ "$si_handler_restore" == 1 || "$si_combined" == 1 ]]; then helper_args+=(--restore-alias);fi
  [[ "$si_epilogue" != 1 ]] || helper_args+=(--epilogue)
  [[ "$si_transfer_prefix" != 1 ]] || helper_args+=(--transfer-prefix)
  [[ "$si_transfer_return" != 1 ]] || helper_args+=(--transfer-return)
  [[ "$si_alarm" != 1 ]] || helper_args+=(--alarm)
  [[ "$si_callback_prefix" != 1 ]] || helper_args+=(--callback-prefix)
  python3 "$here/apply_si_roots_v669.py" "$nw" "$dol" "$elf" "${helper_args[@]}"
fi
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$nw/nWiiRuntime/include" -I"$nw/nWiiAnalyzer/include" -I"$nw/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$nw/nWiiRuntime/src/core/loader.cpp" "$nw/nWiiAnalyzer/src/analyzer.cpp" \
  "$nw/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$nw/nWiiAnalyzer/src/signature_scanner.cpp" "$nw/nWiiRecomp/src/recompiler.cpp" "$nw/nWiiRecomp/src/symbols.cpp" \
  -o "$work/translator" > "$work/build.log" 2>&1 || { echo "V572 full-image translator build failed";exit 1; }
timeout 300s "$work/translator" "$dol" "$work/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay "${external_args[@]}" --generate "$nw/nWiiRuntime" > "$work/generate.log" 2>&1 || { grep -Ex 'SC translation overlay conflict|SC source ambiguous|SC source missing|SC source overlap|SC section geometry|SC vector return|SC vector control flow|SC overlay rejected|SC overlay analysis rejected|SC overlay instruction coverage rejected|SC overlay overlaps trusted span|IRQ overlay rejected|IRQ overlay overlaps trusted span|IRQ overlay analysis rejected|IRQ overlay instruction coverage rejected' "$work/generate.log" || true;echo "V572 full-image translation failed";exit 1; }
[[ "$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | wc -l)" -ge 20 ]]
if [[ "$mode" != translation-only && "$mode" != --prepare-mi && "$mode" != --prepare-report ]]; then
  if [[ "$mode" == --run-dsp-return || "$mode" == --run-mi || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
    if [[ "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
      if [[ "$open_request" == 1 ]]; then
        python3 "$here/prepare_v641_open_request.py" "$dol" "$elf" "$work/generated"
      else
        python3 "$here/prepare_v629_stm_open.py" "$dol" "$elf" "$work/generated"
      fi
    elif [[ "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client ]]; then
      python3 "$here/prepare_v625_ipc_client.py" "$dol" "$elf" "$work/generated"
    elif [[ "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable ]]; then
      python3 "$here/prepare_v616_irq_enable.py" "$dol" "$elf" "$work/generated"
    elif [[ "$mode" == --prepare-arena || "$mode" == --run-arena ]]; then
      python3 "$here/prepare_v609_arena_clear.py" "$dol" "$elf" "$work/generated"
    elif [[ "$mode" == --prepare-report-observer || "$mode" == --run-report ]]; then
      python3 "$here/prepare_v603_boot_report.py" "$dol" "$elf" "$work/generated"
    elif [[ "$mode" == --run-mi ]]; then
      python3 "$here/prepare_v591_memory_init.py" "$dol" "$elf" "$work/generated"
    else
      python3 "$here/prepare_v581_dsp_return.py" "$dol" "$work/generated"
    fi
  else
    python3 "$here/prepare_v574_dsp_sc.py" "$dol" "$work/generated"
  fi
  if [[ "$external_entry" == 1 ]]; then
    python3 "$here/prepare_v663_external_entry.py" "$dol" "$elf" "$work/generated"
    if [[ "$external_capture" == 1 ]]; then python3 "$here/prepare_v751_cold_capture.py" "$work/generated";fi
    if [[ "$si_dispatch" == 1 ]]; then python3 "$here/prepare_v667_si_dispatch.py" "$dol" "$elf" "$work/generated";fi
    if [[ "$si_ack" == 1 ]]; then
      python3 "$here/prepare_v672_si_ack_route.py" "$dol" "$elf" "$work/generated"
      python3 "$here/prepare_v680_si_helper.py" "$dol" "$elf" "$work/generated"
      python3 "$here/prepare_v688_si_second.py" "$dol" "$elf" "$work/generated"
      python3 "$here/prepare_v693_si_nested.py" "$dol" "$elf" "$work/generated"
      if [[ "$si_os_leaves" == 1 ]]; then python3 "$here/prepare_v709_os_leaves.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_handler_return" == 1 ]]; then python3 "$here/prepare_v726_handler_return.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_handler_restore" == 1 ]]; then python3 "$here/prepare_v738_handler_restore.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_handler_time" == 1 ]]; then python3 "$here/prepare_v742_handler_time.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_combined" == 1 ]]; then python3 "$here/prepare_v760_combined_handler.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_epilogue" == 1 ]]; then python3 "$here/prepare_v767_live_epilogue.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_transfer_prefix" == 1 ]]; then python3 "$here/prepare_v768_transfer_prefix.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_transfer_return" == 1 ]]; then python3 "$here/prepare_v777_transfer_return.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_transfer_suffix" == 1 ]]; then python3 "$here/prepare_v778_transfer_suffix.py" "$work/generated";fi
      if [[ "$si_alarm" == 1 ]]; then python3 "$here/prepare_v786_alarm_return.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_alarm_suffix" == 1 ]]; then python3 "$here/prepare_v789_alarm_suffix.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_callback_prefix" == 1 ]]; then python3 "$here/prepare_v807_callback_prefix.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_callback_time" == 1 ]]; then python3 "$here/prepare_v813_callback_time.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_callback_frontier" == 1 ]]; then python3 "$here/prepare_v831_callback_frontier.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_wireless_wrapper" == 1 ]]; then python3 "$here/prepare_v847_wireless_wrapper.py" "$dol" "$elf" "$work/generated";fi
      if [[ "$si_callback_return" == 1 ]]; then python3 "$here/prepare_v850_callback_return.py" "$dol" "$elf" "$work/generated";fi
    fi
  fi
  cat > "$work/probe.cpp" <<'CPP'
#include "runtime/cpu_context.h"
#include "undercover/wii_full_start_probe_v419.h"
void instantiate(nwii::runtime::CPUContext& cpu){
    undercover::wii::v419::observe(cpu.pc,cpu);
    undercover::wii::v574::try_sc(cpu);
}
CPP
  if [[ "$si_callback_prefix" == 1 ]]; then
    cat >> "$work/probe.cpp" <<'CPP'
void instantiate_callback(nwii::runtime::CPUContext& cpu){
    undercover::wii::v807::before(cpu,cpu.pc,0u);
}
CPP
  fi
  if [[ "$si_callback_time" == 1 ]]; then
    cat >> "$work/probe.cpp" <<'CPP'
void instantiate_callback_time(nwii::runtime::CPUContext& cpu){
    undercover::wii::v813::before(cpu,cpu.pc,0u);
}
CPP
  fi
  if [[ "$si_callback_frontier" == 1 ]]; then
    cat >> "$work/probe.cpp" <<'CPP'
void instantiate_callback_frontier(nwii::runtime::CPUContext& cpu){
    undercover::wii::v831::before(cpu,cpu.pc,0u);
}
CPP
  fi
  if [[ "$si_wireless_wrapper" == 1 ]]; then
    cat >> "$work/probe.cpp" <<'CPP'
void instantiate_wireless(nwii::runtime::CPUContext& cpu){
    undercover::wii::v847::before(cpu,cpu.pc,0u);
    undercover::wii::v847::observe(cpu.pc,cpu);
    undercover::wii::v847::start(cpu,cpu.pc,0u,true,3u);
}
CPP
  fi
  if [[ "$si_callback_return" == 1 ]]; then
    cat >> "$work/probe.cpp" <<'CPP'
void instantiate_callback_return(nwii::runtime::CPUContext& cpu){
    undercover::wii::v850::capture(cpu,cpu.pc,0u,6u);
    undercover::wii::v850::start(cpu,cpu.pc,0u,true);
    undercover::wii::v850::observe(cpu.pc,cpu);
    undercover::wii::v850::before(cpu,cpu.pc,0u);
    undercover::wii::v850::poll(cpu);
    undercover::wii::v850::dispatch_resume(cpu,cpu.pc,0u);
    undercover::wii::v850::handler_resume(cpu,cpu.pc,0u);
}
CPP
  fi
  g++ -std=c++20 -fsyntax-only -I"$work/generated/nWiiRuntime/include" "$work/probe.cpp" > "$work/probe.log" 2>&1 || { if [[ "$si_transfer_return" == 1 ]]; then python3 "$here/diagnose_transfer_syntax_v779.py" "$work/probe.log";fi;echo "V574 full observer syntax failed";exit 1; }
  echo "V574_FULL_SC_PREP owner=1 full_image=1 observer=1 syntax=1 link=0 execution=0 boot_verified=0"
else
  python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --owner "$dol"
fi
echo "V572_FULL_SC_TRANSLATION owner=1 full_image=1 vector=7 direct_only=1 link=0 execution=0 boot_verified=0"
if [[ ${#external_args[@]} == 1 ]]; then
  python3 "$here/audit_v662_external_overlay.py" "$dol" "$work/generated"
fi
if [[ "$mode" == --prepare-report || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/audit_v594_report_translation.py" "$dol" "$elf" "$work/generated"
fi
if [[ "$mode" == --prepare-mi || "$mode" == --run-mi || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
  python3 "$here/audit_v584_bat_translation.py" "$dol" "$work/generated"
fi

if [[ "$mode" == --run-dsp-sc || "$mode" == --run-dsp-return || "$mode" == --run-mi || "$mode" == --run-report || "$mode" == --run-arena || "$mode" == --run-irq-enable || "$mode" == --run-ipc-client || "$mode" == --run-stm-open ]]; then
  bash "$here/run_private_full_link.sh" "$work/generated" "$work/native-build"
  if [[ "$mode" == --run-dsp-return || "$mode" == --run-mi || "$mode" == --prepare-report-observer || "$mode" == --run-report || "$mode" == --prepare-arena || "$mode" == --run-arena || "$mode" == --prepare-irq-enable || "$mode" == --run-irq-enable || "$mode" == --prepare-ipc-client || "$mode" == --run-ipc-client || "$mode" == --prepare-stm-open || "$mode" == --run-stm-open ]]; then
    target=dsp-return; [[ "$mode" != --run-mi ]] || target=mi-return
    [[ "$mode" != --run-report ]] || target=report-return
    [[ "$mode" != --run-arena ]] || target=arena-return
    [[ "$mode" != --run-irq-enable ]] || target=irq-enable-return
    [[ "$mode" != --run-ipc-client ]] || target=ipc-client-return
    [[ "$mode" != --run-stm-open ]] || target=stm-open
    [[ "$open_request" != 1 ]] || target=open-request
    [[ "$external_entry" != 1 ]] || target=irq-pending-entry
    [[ "$external_capture" != 1 ]] || target=irq-pending-capture
    [[ "$si_dispatch" != 1 ]] || target=irq-si-dispatch
    [[ "$si_ack" != 1 ]] || target=irq-si-ack
    [[ "$si_postack" != 1 ]] || target=irq-si-postack
    [[ "$si_os_leaves" != 1 ]] || target=irq-si-os-leaves
    [[ "$si_handler_return" != 1 ]] || target=irq-si-handler-return
    [[ "$si_handler_restore" != 1 ]] || target=irq-si-handler-restore
    [[ "$si_handler_time" != 1 ]] || target=irq-si-handler-time
    [[ "$si_time_suffix" != 1 ]] || target=irq-si-time-suffix
    [[ "$si_combined" != 1 ]] || target=irq-si-combined
    [[ "$si_captured" != 1 ]] || target=irq-si-captured
    [[ "$si_epilogue" != 1 ]] || target=irq-si-epilogue
    [[ "$si_transfer_prefix" != 1 ]] || target=irq-si-transfer-prefix
    [[ "$si_transfer_return" != 1 ]] || target=irq-si-transfer-return
    [[ "$si_transfer_suffix" != 1 ]] || target=irq-si-transfer-suffix
    [[ "$si_alarm" != 1 ]] || target=irq-si-alarm
    [[ "$si_alarm_suffix" != 1 ]] || target=irq-si-alarm-suffix
    [[ "$si_callback_prefix" != 1 ]] || target=irq-si-callback-prefix
    [[ "$si_callback_time" != 1 ]] || target=irq-si-callback-time
    [[ "$si_callback_frontier" != 1 ]] || target=irq-si-callback-frontier
    bash "$here/run_v575_dsp_sc_launch.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" "$target"
  else
    bash "$here/run_v575_dsp_sc_launch.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run"
  fi
fi
