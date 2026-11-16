#!/usr/bin/env bash
# Original Wii EXI polling prefix, native NWiiRecomp only; delete game-derived fixtures and generated code on exit.
set -euo pipefail
if (( $# != 2 ));then echo "Usage: $0 ISOLATED_NWII_ROOT ORIGINAL_WII_DOL" >&2; exit 2; fi
root="$(cd "$1" && pwd)"; owner="$(realpath "$2")"; here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/make_exi_poll_v65.py" "$owner" "$work/private.dol"
cxx="${CXX:-g++}"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O0 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
 "$here/generate_exi_poll_v65.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
 "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
 "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" \
 "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"; "$work/generator" "$work/private.dol" "$work/generated"
python3 "$here/test_exi_guards_v65.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V65_SANITIZE:-0}" == 1 ]]; then flags=( -O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer ); fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
 -I"$root/nWiiRuntime/include" "$here/test_exi_poll_v65.cpp" \
 "$work/generated/output.cpp" "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native"
"$work/native" "$work/private.dol"
