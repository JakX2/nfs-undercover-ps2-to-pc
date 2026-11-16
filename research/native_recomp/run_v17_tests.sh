#!/usr/bin/env bash
# Reproducible source-only V17 native startup-hardware test.
# Proprietary owner DOL slices and generated game C++ remain temporary.
set -euo pipefail
if (( $# < 1 || $# > 2 )); then
  echo 'Usage: run_v17_tests.sh NWIIRECOMP_ROOT [OWNER_WII_DOL]' >&2; exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cxx="${CXX:-g++}"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_hardware_dispatch_v17.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$tmp/generator"
python3 "$here/make_hardware_boundary_v17.py" "$tmp/synthetic.dol"
mkdir "$tmp/guard_cases"
python3 "$here/test_hardware_guards_v17.py" "$tmp/generator" "$tmp/synthetic.dol" \
  "$tmp/guard_cases" "$here/make_hardware_boundary_v17.py"
compile_flags=( -O2 )
if [[ "${V17_SANITIZE:-0}" == 1 ]]; then
  compile_flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
run_mode() {
  local mode="$1" dol="$2" own="$3"
  mkdir "$tmp/${mode}_generated"
  "$tmp/generator" "$dol" "$tmp/${mode}_generated" "$mode"
  "$cxx" -std=c++20 "${compile_flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
    -DV17_OWNER="$own" -I"$root/nWiiRuntime/include" \
    "$here/test_hardware_dispatch_v17.cpp" "$tmp/${mode}_generated/output.cpp" \
    -o "$tmp/${mode}_native"
  if "$tmp/${mode}_native" > "$tmp/${mode}.log" 2>&1; then
    tail -1 "$tmp/${mode}.log"
  else
    tail -50 "$tmp/${mode}.log" >&2
    return 1
  fi
}
run_mode synthetic "$tmp/synthetic.dol" 0
if (( $# == 2 )); then
  python3 "$here/audit_hardware_v17.py" "$2" | tail -1
  python3 "$here/make_hardware_boundary_v17.py" "$tmp/owner_PRIVATE.dol" --owner-dol "$2"
  run_mode owner "$tmp/owner_PRIVATE.dol" 1
fi
