#!/usr/bin/env bash
# Actual pinned NWiiRecomp baseline/fixed AOT comparison, no owner inputs.
set -euo pipefail
if [[ $# != 1 ]]; then echo 'usage: run_v438_native_tick.sh PINNED_NWII_ROOT' >&2; exit 2; fi
root="$(realpath "$1")"
here="$(cd "$(dirname "$0")" && pwd)"
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
[[ -z "$(git -C "$root" status --porcelain)" ]]
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
unset NWII_WALLTB
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
for version in baseline fixed; do
  if [[ "$version" == fixed ]]; then
    python3 "$here/apply_native_tick_v438.py" "$root"
    python3 "$here/apply_native_tick_v438.py" "$root"
  fi
  g++ -std=c++20 -O2 -Wno-unused-variable -Wno-sign-compare "${inc[@]}" \
    "$here/generate_native_tick_v438.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
  for mode in nonsplit split; do
    dir="$work/$version-$mode"
    mkdir "$dir"
    "$work/generator" "$dir" "$mode"
    g++ -std=c++20 -O1 -Wall -Wextra -Wno-unused-label -Wno-unused-parameter -Wno-unused-variable \
      -Wno-sign-compare -pthread -fsanitize=address,undefined -fno-pie -no-pie "${inc[@]}" \
      "$here/test_native_tick_v438.cpp" "$dir"/*.cpp \
      "$root/nWiiRuntime/src/core/os_hle_stubs.cpp" "$root/nWiiRuntime/src/hw/mmio_dispatcher.cpp" \
      "$root/nWiiRuntime/src/hw/hw_pi.cpp" "$root/nWiiRuntime/src/hw/hw_ipc.cpp" -o "$dir/native"
    timeout 20s "$dir/native" "$version"
  done
done
