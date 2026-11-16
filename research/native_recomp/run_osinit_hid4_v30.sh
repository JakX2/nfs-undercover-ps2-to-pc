#!/usr/bin/env bash
# Owner-private Wii OSInit→HID4/speculation/nonIEEE native tests.
# Only original-free tool sources belong in the repository.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: bash run_osinit_hid4_v30.sh ISOLATED_NWiiRecomp_ROOT OWNER_WII_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
owner="$(realpath "$2")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
# These installers patch only an ISOLATED NWiiRecomp source tree.
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
if grep -q 'uint32_t hid4 = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  echo 'V30 HID4 state already present; V29 patch superseded; checking V30 invariants'
else
  python3 "$here/apply_perf_sprs_v29.py" "$root"
  python3 "$here/test_perf_patch_guards_v29.py" "$root"
fi
python3 "$here/apply_hid4_fp_v30.py" "$root"
python3 "$here/test_hid4_patch_guards_v30.py" "$root"
python3 "$here/make_osinit_hid4_v30.py" "$owner" "$work/owner_PRIVATE.dol"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O0 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_osinit_hid4_v30.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"
"$work/generator" "$work/owner_PRIVATE.dol" "$work/generated"
python3 "$here/test_osinit_guards_v30.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V30_SANITIZE:-0}" == 1 ]]; then
  flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" "$here/test_osinit_hid4_v30.cpp" \
  "$work/generated/output.cpp" "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native_test"
"$work/native_test" "$work/owner_PRIVATE.dol"
