#!/usr/bin/env bash
# Rebuild and execute genuine Wii __init_data through NWiiRecomp, privately.
set -euo pipefail
if (( $# != 1 && $# != 2 )); then
  echo 'Usage: run_v22_tests.sh NWIIRECOMP_ROOT [PRIVATE_ORIGINAL_WII_DOL]' >&2; exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
 "$here/generate_initdata_dispatch_v22.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" \
 "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
 "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" \
 "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
if (( $# == 2 )); then original=( --owner-dol "$2" ); else original=(); fi
python3 "$here/test_initdata_guards_v22.py" "$work/generator" "${original[@]}"
if (( $# != 2 )); then
  echo 'PASS: V22 source-only table/guard regression (original owner DOL absent)'
  exit 0
fi
flags=( -O2 )
if [[ "${V22_SANITIZE:-0}" == 1 ]]; then
 flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
for mode in original synthetic; do
  mkdir "$work/$mode-generated"
  python3 "$here/make_initdata_slice_v22.py" "$2" "$work/$mode-private.dol" --table-mode "$mode"
  "$work/generator" "$work/$mode-private.dol" "$work/$mode-generated"
  "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
   -I"$root/nWiiRuntime/include" "$here/test_initdata_dispatch_v22.cpp" \
   "$work/$mode-generated/output.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
   -o "$work/$mode-native"
  "$work/$mode-native" "$work/$mode-private.dol" "$mode" > "$work/$mode.log" 2>&1 || {
   tail -80 "$work/$mode.log" >&2; exit 1;
  }
  grep '^PASS: ' "$work/$mode.log" | tail -1
done
