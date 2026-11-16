#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then echo "Usage: $0 NWII_UPSTREAM_ROOT BUILD_DIR" >&2; exit 2; fi
root="$(cd "$1" && pwd)"; mkdir -p "$2"; out="$(cd "$2" && pwd)"
scripts="$(cd "$(dirname "$0")" && pwd)"
# Build offline driver and legacy indexed-load/store tests.
bash "$scripts/build_offline_translator.sh" "$root" "$out"
# Recompiler synthetic tests linked to the original translator components.
c++ -std=c++20 -O1 -I "$root/nWiiRuntime/include" -I "$root/nWiiAnalyzer/include" -I "$root/nWiiRecomp/include" \
  "$scripts/test_v5_emission.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" -o "$out/test_v5_emission"
"$out/test_v5_emission"
c++ -std=c++20 -O2 -I "$root/nWiiRuntime/include" \
  "$scripts/test_v5_runtime.cpp" -o "$out/test_v5_runtime"
"$out/test_v5_runtime"
