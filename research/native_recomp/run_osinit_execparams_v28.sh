#!/usr/bin/env bash
# Test only original Wii OSInit prefix; never distribute DOL slices or generated game C++.
set -euo pipefail
if (( $#!=2 ));then echo 'usage: bash run_osinit_execparams_v28.sh NWiiRecomp-root private-original-DOL' >&2;exit 2;fi
root="$(cd "$1" && pwd)";owner="$(realpath "$2")";here="$(cd "$(dirname "$0")" && pwd)"
cxx="${CXX:-g++}";work="$(mktemp -d)";trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/make_osinit_execparams_v28.py" "$owner" "$work/owner_PRIVATE.dol"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
 "$here/generate_osinit_execparams_v28.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"
"$work/generator" "$work/owner_PRIVATE.dol" "$work/generated"
python3 "$here/test_osinit_guards_v28.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V28_SANITIZE:-0}" == 1 ]];then flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer );fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
 -I"$root/nWiiRuntime/include" "$here/test_osinit_execparams_v28.cpp" \
 "$work/generated/output.cpp" "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native_test"
"$work/native_test" "$work/owner_PRIVATE.dol"
