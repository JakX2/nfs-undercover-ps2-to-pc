#!/usr/bin/env bash
# Actual pinned NWiiRecomp baseline/fixed AOT comparison, no owner inputs.
set -euo pipefail
if [[ $# != 1 ]]; then echo 'usage: run_v456_cache_order.sh PINNED_NWII_ROOT' >&2; exit 2; fi
root="$(realpath "$1")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ -z "$(git -C "$root" status --porcelain)" ]]
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
unset NWII_WALLTB
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
# Exact full-image os-ipc compiler patch order, followed by cache support.
for patch in apply_psq_indexed_patch apply_psq_estimate_and_gqr_v5 apply_verified_elf_spans_v6 \
  apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 \
  apply_perf_sprs_v29 apply_hid_state_v18 apply_fpscr_v19 apply_l2cr_v20 \
  apply_mtmsr_resume_v74 verify_perf_combo_v29 apply_hid4_continuous_v30 \
  apply_cache_continuous_v39 apply_cache_trace_v44 apply_dcbz_v67 apply_cache_order_v456; do
  python3 "$here/$patch.py" "$root"
done
python3 "$here/apply_cache_order_v456.py" "$root"
for version in composed; do
  g++ -std=c++20 -O2 -Wno-unused-variable -Wno-sign-compare "${inc[@]}" \
    "$here/generate_cache_order_v456.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
  for mode in nonsplit split; do
    dir="$work/$version-$mode"
    mkdir "$dir"
    "$work/generator" "$dir" "$mode"
    mode_flags=()
    if [[ "$mode" == split ]]; then mode_flags=(-DV456_SPLIT -I"$dir"); fi
    g++ -std=c++20 -O1 -Wall -Wextra -Wno-unused-label -Wno-unused-parameter -Wno-unused-variable \
      -Wno-sign-compare -pthread -fsanitize=address,undefined -fno-pie -no-pie "${inc[@]}" "${mode_flags[@]}" \
      "$here/test_native_cache_order_v456.cpp" "$dir"/*.cpp \
      "$root/nWiiRuntime/src/core/os_hle_stubs.cpp" "$root/nWiiRuntime/src/hw/mmio_dispatcher.cpp" \
      "$root/nWiiRuntime/src/hw/hw_pi.cpp" "$root/nWiiRuntime/src/hw/hw_ipc.cpp" -o "$dir/native"
    timeout 20s "$dir/native"
  done
done
