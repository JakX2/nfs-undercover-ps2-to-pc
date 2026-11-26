#!/usr/bin/env bash
set -euo pipefail
[[ $# == 1 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ -z "$(git -C "$root" status --porcelain)" ]]
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT
unset NWII_WALLTB
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
for patch in apply_nonsplit_dispatch_v15 apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_hid_state_v18 apply_cache_events_v561 apply_isolated_dcbi_v1276;do
  python3 "$here/$patch.py" "$root"
done
python3 "$here/apply_isolated_dcbi_v1276.py" "$root"
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_isolated_dcbi_v1276.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
for mode in nonsplit split;do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode"
  flags=();if [[ "$mode" == split ]];then flags=(-DV1276_SPLIT -I"$work/$mode");fi
  g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -pthread "${inc[@]}" "${flags[@]}" \
    "$here/test_native_isolated_dcbi_v1276.cpp" "$work/$mode"/*.cpp \
    "$root/nWiiRuntime/src/core/os_hle_stubs.cpp" "$root/nWiiRuntime/src/hw/mmio_dispatcher.cpp" \
    "$root/nWiiRuntime/src/hw/hw_pi.cpp" "$root/nWiiRuntime/src/hw/hw_ipc.cpp" -o "$work/native"
  ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 20s "$work/native"
done
