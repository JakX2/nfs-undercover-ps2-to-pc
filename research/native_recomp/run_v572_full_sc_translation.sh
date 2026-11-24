#!/usr/bin/env bash
# Full-image translation only; no owner C++ or detailed logs leave scratch.
set -euo pipefail
[[ $# == 3 ]] || exit 2
root="$(realpath "$1")"; dol="$(realpath "$2")"; elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf -- "$work"' EXIT; umask 077
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ "$(sha256sum "$dol" | cut -d ' ' -f1)" == 16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4 ]]
mkdir "$work/nwii" "$work/generated"
git -C "$root" archive HEAD | tar -x -C "$work/nwii"
nw="$work/nwii"
python3 "$here/make_private_elf_symbol_map.py" "$elf" "$work/symbols.csv"
for p in apply_psq_indexed_patch apply_psq_estimate_and_gqr_v5 apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_perf_sprs_v29 apply_hid_state_v18 apply_fpscr_v19 apply_l2cr_v20 apply_mtmsr_resume_v74 verify_perf_combo_v29 apply_hid4_continuous_v30 apply_cache_continuous_v39 apply_cache_trace_v44 apply_dcbz_v67 apply_cache_order_v456 apply_data_cache_invalidate_v532 apply_native_lowmem_v63 apply_syscall_pc_v26 apply_syscall_transfer_v461; do
  python3 "$here/$p.py" "$nw" > "$work/patch.log" 2>&1 || { echo "V572 full-image source patch failed: $p";exit 1; }
done
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$nw/nWiiRuntime/include" -I"$nw/nWiiAnalyzer/include" -I"$nw/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$nw/nWiiRuntime/src/core/loader.cpp" "$nw/nWiiAnalyzer/src/analyzer.cpp" \
  "$nw/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$nw/nWiiAnalyzer/src/signature_scanner.cpp" "$nw/nWiiRecomp/src/recompiler.cpp" "$nw/nWiiRecomp/src/symbols.cpp" \
  -o "$work/translator" > "$work/build.log" 2>&1 || { echo "V572 full-image translator build failed";exit 1; }
timeout 300s "$work/translator" "$dol" "$work/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay --generate "$nw/nWiiRuntime" > "$work/generate.log" 2>&1 || { grep -Ex 'SC translation overlay conflict|SC source ambiguous|SC source missing|SC source overlap|SC section geometry|SC vector return|SC vector control flow|SC overlay rejected|SC overlay analysis rejected|SC overlay instruction coverage rejected|SC overlay overlaps trusted span' "$work/generate.log" || true;echo "V572 full-image translation failed";exit 1; }
[[ "$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | wc -l)" -ge 20 ]]
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --owner "$dol"
echo "V572_FULL_SC_TRANSLATION owner=1 full_image=1 vector=7 direct_only=1 link=0 execution=0 boot_verified=0"
