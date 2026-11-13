#!/usr/bin/env bash
# Original-free native execution of guest PowerPC __OSPSInit call graph.
# Owner-provided game data and generated game C++ stay in a private temp dir.
set -euo pipefail
if (( $# < 1 || $# > 2 )); then
    echo 'Usage: bash run_v18_tests.sh NWIIRECOMP_ROOT [OWNER_WII_DOL]' >&2
    exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_hid_state_v18.py" "$root"
python3 "$here/apply_hid_state_v18.py" "$root" # idempotence
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
    "$here/generate_psinit_dispatch_v18.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" \
    "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
    "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
python3 "$here/test_psinit_guards_v18.py" "$work/generator" "$root"
flags=( -O2 )
if [[ "${V18_SANITIZE:-0}" == 1 ]]; then
    flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
run_one() {
    local mode="$1" dol="$2" owner_flag="$3"
    mkdir "$work/${mode}-generated"
    "$work/generator" "$dol" "$work/${mode}-generated" "$mode"
    "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
        -DV18_OWNER="$owner_flag" -I"$root/nWiiRuntime/include" \
        "$here/test_psinit_dispatch_v18.cpp" "$work/${mode}-generated/output.cpp" \
        -o "$work/${mode}-native"
    "$work/${mode}-native" > "$work/${mode}.log" 2>&1 || { tail -60 "$work/${mode}.log" >&2; return 1; }
    tail -1 "$work/${mode}.log"
}
python3 "$here/make_psinit_slice_v18.py" "$work/synthetic.dol"
run_one synthetic "$work/synthetic.dol" 0
if (( $# == 2 )); then
    python3 "$here/make_psinit_slice_v18.py" "$work/owner_PRIVATE.dol" --owner-dol "$2"
    run_one owner "$work/owner_PRIVATE.dol" 1
fi
