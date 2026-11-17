#!/usr/bin/env bash
# Recovered original-free V26 continuous __start native runner.
# Original DOL/code and native generated objects exist only in mktemp.
set -euo pipefail
if (( $#!=1 && $#!=2 )); then
  echo 'Usage: bash run_v26_recovered_tests.sh NWII_ROOT [private-original-DOL]' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
cxx="g++"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
if ! grep -q 'uint32_t l2cr = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 "$here/apply_hid_state_v18.py" "$root"
  python3 "$here/apply_fpscr_v19.py" "$root"
fi
python3 "$here/apply_l2cr_v20.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_time_v26_recovered.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
flags=( -O2 )
if [[ -v V26R_SANITIZE && "$V26R_SANITIZE" == "1" ]]; then
  flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
for mode in synthetic owner; do
  if [[ "$mode" == owner && $# != 2 ]]; then continue; fi
  image="$work/$mode.dol"
  if [[ "$mode" == owner ]]; then
    python3 "$here/make_start_to_time_v26_recovered.py" "$image" --owner-dol "$2"
    python3 "$here/test_v26_recovered_geometry.py" "$image" --owner-dol "$2"
  else
    python3 "$here/make_start_to_time_v26_recovered.py" "$image"
    python3 "$here/test_v26_recovered_geometry.py" "$image"
  fi
  mkdir "$work/$mode-generated"
  "$work/generator" "$image" "$work/$mode-generated" "$mode" > "$work/$mode.generator.log" 2>&1 || {
    if [[ "$mode" == synthetic ]]; then tail -50 "$work/$mode.generator.log"; fi
    echo "Recovered V26 generator failed: $mode" >&2
    exit 1
  }
  "$cxx" -std=c++20 -O2 -Wall -Wextra -Werror \
    -Wno-type-limits -Wno-unused-label \
    -I"$root/nWiiRuntime/include" \
    "$here/test_start_to_time_v26_recovered.cpp" \
    "$work/$mode-generated/output.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" \
    -o "$work/$mode-native" > "$work/$mode.compile.log" 2>&1 || {
      if [[ "$mode" == synthetic ]]; then tail -45 "$work/$mode.compile.log"; fi
      echo "Recovered V26 native compile failed: $mode" >&2
      exit 1
    }
  "$work/$mode-native" "$image" "$mode" > "$work/$mode.native.log" 2>&1 || {
    if [[ "$mode" == synthetic ]]; then tail -50 "$work/$mode.native.log"; fi
    echo "Recovered V26 native test failed: $mode (private log withheld)" >&2
    exit 1
  }
  grep -q '^PASS:' "$work/$mode.native.log" || { echo "Missing V26 native PASS"; exit 1; }
  echo "PASS: recovered V26 native startup test mode=$mode"
done
