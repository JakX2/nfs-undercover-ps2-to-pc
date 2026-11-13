#!/usr/bin/env bash
# Original-free synthetic callgraph test; optional owner-private original Wii DOL.
set -euo pipefail
if (( $# < 1 || $# > 2 )); then
    echo "Usage: $0 NWIIRECOMP_SOURCE_DIR [OWNER_ORIGINAL_WII_DOL]" >&2
    exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$work/synthetic" "$work/owner"
CXX="${CXX:-g++}"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
base=( "$CXX" -std=c++20 -Wall -Wextra -Wno-unused-label "${inc[@]}" )
# Upstream NWiiRecomp is not -Werror clean; generated tests are.
"${base[@]}" -O2 -Wno-sign-compare -Wno-unused-variable \
    "$here/recompile_callgraph_v14.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" \
    "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
    "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/extract"
python3 "$here/make_synthetic_callgraph_v14.py" "$work/synthetic.dol"
python3 "$here/test_callgraph_guard_v14.py" "$work/extract" "$work/synthetic.dol" "$work"
"$work/extract" "$work/synthetic.dol" "$work/synthetic" 80004000:24 80004018:8
flags=( -O2 -Werror )
if [[ "${V14_SANITIZE:-0}" == "1" ]]; then
    flags=( -O1 -g -Werror -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"${base[@]}" "${flags[@]}" "$here/test_synthetic_callgraph_v14.cpp" \
    "$work/synthetic/func_80004000.cpp" "$work/synthetic/func_80004018.cpp" \
    -o "$work/synthetic_test"
"$work/synthetic_test"
if (( $# == 2 )); then
    # Only the selected two owner-original functions are generated, into a
    # transient private directory that the trap wipes on exit.
    "$work/extract" "$2" "$work/owner" 8007ADAC:28 8007ADC8:112
    "${base[@]}" "${flags[@]}" "$here/test_real_callgraph_v14.cpp" \
        "$work/owner/func_8007ADAC.cpp" "$work/owner/func_8007ADC8.cpp" \
        "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/owner_test"
    "$work/owner_test" "$2"
fi
