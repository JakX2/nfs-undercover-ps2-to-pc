#!/usr/bin/env bash
# Source-only regression: original Wii OSInit through authentic exception-vector memcpy.
# Private original DOL slices and game-derived output.cpp are deleted on exit.
set -euo pipefail
if (( $# != 2 )); then
  printf 'Usage: bash %s ISOLATED_NWII_ROOT OWNER_WII_DOL\n' "$0" >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
owner="$(realpath "$2")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
if ! grep -q 'uint32_t hid4 = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 "$here/apply_perf_sprs_v29.py" "$root"
  python3 "$here/test_perf_patch_guards_v29.py" "$root"
fi
python3 "$here/apply_hid4_fp_v30.py" "$root"
python3 "$here/test_hid4_patch_guards_v30.py" "$root"
python3 "$here/make_osinit_vectorcopy_v42.py" "$owner" "$work/private_owner.dol"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O0 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_osinit_vectorcopy_v42.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"
"$work/generator" "$work/private_owner.dol" "$work/generated"
python3 "$here/test_osinit_guards_v42.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V42_SANITIZE:-0}" == 1 ]]; then
  flags=( -O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" "$here/test_osinit_vectorcopy_v42.cpp" \
  "$work/generated/output.cpp" "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native_test"
if ! "$work/native_test" "$work/private_owner.dol" >"$work/native.log" 2>&1; then
  tail -85 "$work/native.log" >&2
  exit 1
fi
grep '^PASS:' "$work/native.log"
