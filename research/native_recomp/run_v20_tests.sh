#!/usr/bin/env bash
# Source-only native test runner. Owner DOL never leaves mktemp's private slice.
set -euo pipefail
if (( $# < 1 || $# > 2 )); then
    echo "Usage: bash run_v20_tests.sh NWIIRECOMP_SOURCE_ROOT [OWNER_ORIGINAL_DOL]" >&2
    exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
# We patch ONLY this owner-local NWiiRecomp checkout; isolate it from other work.
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
if ! grep -q 'uint32_t l2cr = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
    python3 "$here/apply_hid_state_v18.py" "$root"
    python3 "$here/apply_fpscr_v19.py" "$root"
fi
python3 "$here/apply_l2cr_v20.py" "$root"
python3 "$here/apply_l2cr_v20.py" "$root"  # assert idempotence
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
    "$here/generate_cache_dispatch_v20.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" \
    "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
    "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
optional_owner=()
if (( $# == 2 )); then optional_owner=( --owner-dol "$2" ); fi
python3 "$here/test_cache_guards_v20.py" "$work/generator" "$root" "${optional_owner[@]}"
flags=( -O2 )
if [[ "${V20_SANITIZE:-0}" == 1 ]]; then
    flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror \
    -I"$root/nWiiRuntime/include" "$here/test_l2cr_v20.cpp" -o "$work/l2cr_test"
"$work/l2cr_test"
run_case() {
    local mode="$1" dol="$2" is_owner="$3"
    mkdir "$work/${mode}-generated"
    "$work/generator" "$dol" "$work/${mode}-generated" "$mode"
    "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
        -DV20_OWNER="$is_owner" -I"$root/nWiiRuntime/include" \
        "$here/test_cache_dispatch_v20.cpp" "$work/${mode}-generated/output.cpp" \
        -o "$work/${mode}-native"
    # Existing NWiiRecomp dispatcher prints 128 debug PC histories on exit.
    # Keep the build summary concise, but preserve failures for inspection.
    "$work/${mode}-native" > "$work/${mode}.log" 2>&1 || {
        tail -35 "$work/${mode}.log" >&2; return 1;
    }
    grep '^PASS: ' "$work/${mode}.log" | tail -1
}
python3 "$here/make_cache_slice_v20.py" "$work/synthetic.dol"
run_case synthetic "$work/synthetic.dol" 0
if (( $# == 2 )); then
    python3 "$here/make_cache_slice_v20.py" "$work/owner_PRIVATE.dol" --owner-dol "$2"
    run_case owner "$work/owner_PRIVATE.dol" 1
fi
