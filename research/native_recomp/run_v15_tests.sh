#!/usr/bin/env bash
# Build from an owner-controlled NWiiRecomp checkout. All generated code stays
# in private temporary storage; nothing here publishes original Wii game code.
set -euo pipefail
if (( $# != 1 && $# != 2 )); then
    echo 'Usage: bash run_v15_tests.sh NWIIRECOMP_SOURCE_ROOT [ORIGINAL_OWNER_DOL]' >&2
    exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
cxx="${CXX:-g++}"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
# Existing analyzer warnings are upstream behavior and intentionally visible.
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
   "${inc[@]}" "$here/generate_dispatch_v15.cpp" \
   "$root/nWiiRuntime/src/core/loader.cpp" \
   "$root/nWiiAnalyzer/src/analyzer.cpp" \
   "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
   "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
   "$root/nWiiRecomp/src/recompiler.cpp" \
   "$root/nWiiRecomp/src/symbols.cpp" -o "$work/gen_dispatch"
python3 "$here/test_guards_v15.py" "$work/gen_dispatch" "$root" "$work"
python3 "$here/make_dispatch_slice_v15.py" "$work/synthetic.dol"
mkdir -p "$work/synthetic_cpp"
"$work/gen_dispatch" "$work/synthetic.dol" "$work/synthetic_cpp" 80004000 24 80004018 8
flags=( -O2 )
if [[ "${V15_SANITIZE:-0}" == 1 ]]; then
    flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
    -DV15_REAL=0 -I"$root/nWiiRuntime/include" \
    "$here/test_full_dispatch_v15.cpp" "$work/synthetic_cpp/output.cpp" -o "$work/test_synth"
"$work/test_synth"
if (( $# == 2 )); then
    # Source contains original PPC opcodes. Keep this output private and delete
    # it when the test exits, including when compilation or tests fail.
    python3 "$here/make_dispatch_slice_v15.py" "$work/owner_PRIVATE.dol" --owner-dol "$2"
    mkdir -p "$work/owner_PRIVATE_cpp"
    "$work/gen_dispatch" "$work/owner_PRIVATE.dol" "$work/owner_PRIVATE_cpp" 8007ADC8 112 8007ADAC 28
    "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
        -DV15_REAL=1 -I"$root/nWiiRuntime/include" \
        "$here/test_full_dispatch_v15.cpp" "$work/owner_PRIVATE_cpp/output.cpp" -o "$work/test_owner"
    "$work/test_owner"
fi
