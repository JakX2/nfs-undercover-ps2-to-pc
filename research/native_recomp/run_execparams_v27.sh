#!/usr/bin/env bash
# Owner-private bounded run: genuine original __OSGetExecParams and memcpy.
set -euo pipefail
if (( $# != 2 ));then echo 'usage: bash run_execparams_v27.sh NWiiRecomp-root owner-original.dol' >&2; exit 2;fi
root="$(cd "$1" && pwd)"; owner="$(realpath "$2")"; here="$(cd "$(dirname "$0")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/make_execparams_v27.py" "$owner" "$work/execparams_private.dol"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_execparams_v27.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"
"$work/generator" "$work/execparams_private.dol" "$work/generated"
python3 "$here/test_execparams_guards_v27.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V27_SANITIZE:-0}" == 1 ]];then flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer );fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
   -I"$root/nWiiRuntime/include" "$here/test_execparams_v27.cpp" \
   "$work/generated/output.cpp" "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native_test"
"$work/native_test" "$work/execparams_private.dol"
