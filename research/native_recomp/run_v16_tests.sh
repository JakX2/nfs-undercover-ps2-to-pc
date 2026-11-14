#!/usr/bin/env bash
# Build from locally owned NWiiRecomp and optional SHA-pinned original Wii DOL.
# All private DOL slices and generated C++ remain in mktemp and are deleted.
set -euo pipefail
if (( $# < 1 || $# > 2 )); then
    echo 'Usage: bash run_v16_tests.sh NWIIRECOMP_ROOT [OWNER_ORIGINAL_WII_DOL]' >&2
    exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cxx="${CXX:-g++}"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
    "${inc[@]}" "$here/generate_startup_dispatch_v16.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" \
    "$root/nWiiAnalyzer/src/analyzer.cpp" \
    "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
    "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
    "$root/nWiiRecomp/src/recompiler.cpp" \
    "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generate_startup"
python3 "$here/make_startup_boundary_v16.py" "$work/synthetic_startup.dol"
python3 "$here/test_startup_guards_v16.py" "$work/generate_startup" \
    "$here/make_startup_boundary_v16.py" "$work"
flags=( -O2 )
if [[ "${V16_SANITIZE:-0}" == "1" ]]; then
    flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
run_one() {
    local mode="$1" dol="$2" owner_mode="$3"
    mkdir "$work/${mode}_generated"
    "$work/generate_startup" "$dol" "$work/${mode}_generated" "$mode"
    "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
      -DV16_OWNER="$owner_mode" -I"$root/nWiiRuntime/include" \
      "$here/test_startup_dispatch_v16.cpp" \
      "$work/${mode}_generated/output.cpp" -o "$work/${mode}_test"
    # NWiiRecomp prints debug history after each dispatch; retain only final
    # result for a concise log, but preserve the full log on failure.
    if "$work/${mode}_test" > "$work/${mode}.log" 2>&1; then
        tail -1 "$work/${mode}.log"
    else
        tail -40 "$work/${mode}.log" >&2
        return 1
    fi
}
run_one synthetic "$work/synthetic_startup.dol" 0
if (( $# == 2 )); then
    python3 "$here/audit_startup_v16.py" "$2"
    python3 "$here/make_startup_boundary_v16.py" "$work/owner_PRIVATE.dol" --owner-dol "$2"
    run_one owner "$work/owner_PRIVATE.dol" 1
fi
