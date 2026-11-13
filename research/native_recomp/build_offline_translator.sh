#!/usr/bin/env bash
# Build NWiiRecomp's existing analyzer/recompiler without GUI/SDL/TOML downloads.
# This builds the ahead-of-time translator only, not a playable Wii runtime.
set -euo pipefail
if [[ $# -ne 2 ]]; then echo 'Usage: build_offline_translator.sh UPSTREAM_NWII_SOURCE_ROOT OUTPUT_BIN_DIR' >&2; exit 2; fi
root="$(cd "$1" && pwd)"
output="$2"
mkdir -p "$output"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
compiler="${CXX:-g++}"
src=(
 "$root/nWiiRuntime/src/core/loader.cpp"
 "$root/nWiiAnalyzer/src/analyzer.cpp"
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp"
 "$root/nWiiAnalyzer/src/signature_scanner.cpp"
 "$root/nWiiRecomp/src/symbols.cpp"
 "$root/nWiiRecomp/src/recompiler.cpp"
)
includes=(-I "$root/nWiiRuntime/include" -I "$root/nWiiAnalyzer/include" -I "$root/nWiiRecomp/include")
"$compiler" -std=c++20 -O2 "${includes[@]}" "$script_dir/offline_recompiler_driver.cpp" "${src[@]}" -o "$output/offline_recompiler_driver"
"$compiler" -std=c++20 -O1 "${includes[@]}" "$script_dir/test_psq_indexed_emission.cpp" "${src[@]}" -o "$output/test_psq_indexed_emission"
"$output/test_psq_indexed_emission"
