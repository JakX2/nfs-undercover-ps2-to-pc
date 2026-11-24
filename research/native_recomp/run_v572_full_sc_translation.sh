#!/usr/bin/env bash
# Full-image translation and opt-in bounded DSP SC startup; private scratch only.
set -euo pipefail
[[ $# == 3 || ( $# == 4 && ( "$4" == --prepare-dsp-sc || "$4" == --run-dsp-sc || "$4" == --run-dsp-return || "$4" == --prepare-mi || "$4" == --run-mi || "$4" == --prepare-report ) ) ]] || exit 2
mode="${4:-translation-only}"
root="$(realpath "$1")"; dol="$(realpath "$2")"; elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf -- "$work"' EXIT; umask 077
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]]
mkdir "$work/nwii" "$work/generated"
git -C "$root" archive HEAD | tar -x -C "$work/nwii"
nw="$work/nwii"
if [[ "$mode" == --prepare-mi || "$mode" == --run-mi ]]; then
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
if [[ "$mode" == --run-dsp-return || "$mode" == --run-mi ]]; then
  python3 "$here/apply_aram_binding_v553.py" "$nw" emitter > "$work/patch.log" 2>&1 || { echo "V581 ARAM emitter patch failed";exit 1; }
fi
if [[ "$mode" == --prepare-mi || "$mode" == --run-mi ]]; then
  python3 "$here/apply_bat_roots_v586.py" "$nw"
  python3 "$here/apply_bat_registers_v65.py" "$nw" > "$work/patch.log" 2>&1 || { echo "V584 BAT source patch failed";exit 1; }
  g++ -std=c++20 -O1 -Wall -Wextra -Werror -I"$nw/nWiiRuntime/include" "$here/test_bat_registers_v65.cpp" -o "$work/bat-registers" > "$work/bat-compile.log" 2>&1 || { echo "V584 BAT register test build failed";exit 1; }
  "$work/bat-registers"
fi
if [[ "$mode" == --prepare-report ]]; then
  python3 "$here/make_v594_boot_report_geometry.py" "$dol" "$elf"
  python3 "$here/apply_report_table_v594.py" "$nw" "$dol" "$elf"
fi
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$nw/nWiiRuntime/include" -I"$nw/nWiiAnalyzer/include" -I"$nw/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$nw/nWiiRuntime/src/core/loader.cpp" "$nw/nWiiAnalyzer/src/analyzer.cpp" \
  "$nw/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$nw/nWiiAnalyzer/src/signature_scanner.cpp" "$nw/nWiiRecomp/src/recompiler.cpp" "$nw/nWiiRecomp/src/symbols.cpp" \
  -o "$work/translator" > "$work/build.log" 2>&1 || { echo "V572 full-image translator build failed";exit 1; }
timeout 300s "$work/translator" "$dol" "$work/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay --generate "$nw/nWiiRuntime" > "$work/generate.log" 2>&1 || { grep -Ex 'SC translation overlay conflict|SC source ambiguous|SC source missing|SC source overlap|SC section geometry|SC vector return|SC vector control flow|SC overlay rejected|SC overlay analysis rejected|SC overlay instruction coverage rejected|SC overlay overlaps trusted span' "$work/generate.log" || true;echo "V572 full-image translation failed";exit 1; }
[[ "$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | wc -l)" -ge 20 ]]
if [[ "$mode" != translation-only && "$mode" != --prepare-mi && "$mode" != --prepare-report ]]; then
  if [[ "$mode" == --run-dsp-return || "$mode" == --run-mi ]]; then
    if [[ "$mode" == --run-mi ]]; then
      python3 "$here/prepare_v591_memory_init.py" "$dol" "$elf" "$work/generated"
    else
      python3 "$here/prepare_v581_dsp_return.py" "$dol" "$work/generated"
    fi
  else
    python3 "$here/prepare_v574_dsp_sc.py" "$dol" "$work/generated"
  fi
  cat > "$work/probe.cpp" <<'CPP'
#include "runtime/cpu_context.h"
#include "undercover/wii_full_start_probe_v419.h"
void instantiate(nwii::runtime::CPUContext& cpu){
    undercover::wii::v419::observe(cpu.pc,cpu);
    undercover::wii::v574::try_sc(cpu);
}
CPP
  g++ -std=c++20 -fsyntax-only -I"$work/generated/nWiiRuntime/include" "$work/probe.cpp" > "$work/probe.log" 2>&1 || { echo "V574 full observer syntax failed";exit 1; }
  echo "V574_FULL_SC_PREP owner=1 full_image=1 observer=1 syntax=1 link=0 execution=0 boot_verified=0"
else
  python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --owner "$dol"
fi
echo "V572_FULL_SC_TRANSLATION owner=1 full_image=1 vector=7 direct_only=1 link=0 execution=0 boot_verified=0"
if [[ "$mode" == --prepare-report ]]; then
  python3 "$here/audit_v594_report_translation.py" "$dol" "$elf" "$work/generated"
fi
if [[ "$mode" == --prepare-mi || "$mode" == --run-mi ]]; then
  python3 "$here/audit_v584_bat_translation.py" "$dol" "$work/generated"
fi

if [[ "$mode" == --run-dsp-sc || "$mode" == --run-dsp-return || "$mode" == --run-mi ]]; then
  bash "$here/run_private_full_link.sh" "$work/generated" "$work/native-build"
  if [[ "$mode" == --run-dsp-return || "$mode" == --run-mi ]]; then
    target=dsp-return; [[ "$mode" != --run-mi ]] || target=mi-return
    bash "$here/run_v575_dsp_sc_launch.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" "$target"
  else
    bash "$here/run_v575_dsp_sc_launch.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run"
  fi
fi
