#!/usr/bin/env bash
# Original-free synthetic FPR init; optional owner-private Undercover Wii DOL.
set -euo pipefail
if (( $# < 1 || $# > 2 )); then
    echo 'Usage: bash run_v19_tests.sh NWIIRECOMP_ROOT [PRIVATE_ORIGINAL_WII_DOL]' >&2
    exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_hid_state_v18.py" "$root"
python3 "$here/apply_fpscr_v19.py" "$root"
python3 "$here/apply_fpscr_v19.py" "$root"  # assert idempotence
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
    "$here/generate_fprinit_dispatch_v19.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" \
    "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
    "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
python3 "$here/test_fprinit_guards_v19.py" "$work/generator" "$root"
flags=( -O2 )
if [[ "${V19_SANITIZE:-0}" == 1 ]]; then
    flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -I"$root/nWiiRuntime/include" \
    "$here/test_fpscr_fields_v19.cpp" -o "$work/fpscr_fields"
"$work/fpscr_fields"
run_one() {
    local mode="$1" dol="$2" owner_flag="$3"
    mkdir "$work/${mode}-generated"
    "$work/generator" "$dol" "$work/${mode}-generated" "$mode"
    "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
        -DV19_OWNER="$owner_flag" -I"$root/nWiiRuntime/include" \
        "$here/test_fprinit_dispatch_v19.cpp" "$work/${mode}-generated/output.cpp" \
        -o "$work/${mode}-native"
    "$work/${mode}-native" > "$work/${mode}.log" 2>&1 || { tail -40 "$work/${mode}.log" >&2; return 1; }
    tail -1 "$work/${mode}.log"
    if [[ "$owner_flag" == 1 ]]; then
        "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
            -I"$root/nWiiRuntime/include" \
            "$here/test_owner_fpr_branch_v19.cpp" "$work/${mode}-generated/output.cpp" \
            -o "$work/owner-branch"
        "$work/owner-branch" > "$work/branch.log" 2>&1 || { tail -40 "$work/branch.log" >&2; return 1; }
        tail -1 "$work/branch.log"
    fi
}
python3 "$here/make_fprinit_slice_v19.py" "$work/synthetic.dol"
run_one synthetic "$work/synthetic.dol" 0
if (( $# == 2 )); then
    python3 "$here/make_fprinit_slice_v19.py" "$work/owner_PRIVATE.dol" --owner-dol "$2"
    run_one owner "$work/owner_PRIVATE.dol" 1
fi
