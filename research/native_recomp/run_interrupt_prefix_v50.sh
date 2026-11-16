#!/usr/bin/env bash
# Original Wii interrupt prefix native test; no proprietary data published.
set -euo pipefail
if (( $# != 2 )); then
  echo "Usage: bash $0 ISOLATED_NWII_ROOT OWNER_WII_DOL" >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
owner="$(realpath "$2")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/make_interrupt_prefix_v50.py" "$owner" "$work/private.dol"
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O0 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_interrupt_prefix_v50.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/gen"
mkdir "$work/generated"
"$work/gen" "$work/private.dol" "$work/generated"
python3 "$here/test_interrupt_guards_v50.py" "$owner" "$work/gen"
flags=( -O2 )
if [[ "${V50_SANITIZE:-0}" == 1 ]]; then
  flags=( -O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_interrupt_prefix_v50.cpp" \
  "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native"
"$work/native" "$work/private.dol"
