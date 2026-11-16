#!/usr/bin/env bash
# Original-free V23 reproducible native starter and data-initialization test.
# Original Wii code is generated only under mktemp and erased at exit.
set -euo pipefail
if (( $# != 1 && $# != 2 )); then
  echo 'Usage: bash run_v23_tests.sh /private/NWiiRecomp-master [private_original.dol.bin]' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
# All changes are original-free, applied only to the user-supplied local
# NWiiRecomp checkout. The chained patchers reject incompatible versions.
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
if ! grep -q 'uint32_t l2cr = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 "$here/apply_hid_state_v18.py" "$root"
  python3 "$here/apply_fpscr_v19.py" "$root"
fi
python3 "$here/apply_l2cr_v20.py" "$root"
python3 "$here/apply_l2cr_v20.py" "$root" >/dev/null
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_start_to_data_v23.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
if (( $# == 2 )); then optional_owner=(--owner-dol "$2"); else optional_owner=(); fi
python3 "$here/test_start_guards_v23.py" "$work/generator" "${optional_owner[@]}"
flags=( -O2 )
if [[ "${V23_SANITIZE:-0}" == "1" ]]; then
  flags=( -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
for mode in synthetic owner; do
  if [[ "$mode" == "owner" && $# != 2 ]]; then continue; fi
  mkdir "$work/${mode}_generated"
  if [[ "$mode" == "owner" ]]; then
    python3 "$here/make_start_to_data_v23.py" "$work/owner_PRIVATE.dol" --owner-dol "$2"
  else
    python3 "$here/make_start_to_data_v23.py" "$work/synthetic.dol"
  fi
  if [[ "$mode" == "owner" ]]; then input="$work/owner_PRIVATE.dol"; else input="$work/synthetic.dol"; fi
  "$work/generator" "$input" "$work/${mode}_generated" "$mode" > "$work/${mode}_generate.log" 2>&1 || {
    tail -45 "$work/${mode}_generate.log" >&2; exit 1;
  }
  echo "$(grep '^PASS: ' "$work/${mode}_generate.log" | tail -1)"
  "$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
    -I"$root/nWiiRuntime/include" "$here/test_start_to_data_v23.cpp" \
    "$work/${mode}_generated/output.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/${mode}_native"
  "$work/${mode}_native" "$input" "$mode" > "$work/${mode}.log" 2>&1 || {
    tail -65 "$work/${mode}.log" >&2; exit 1;
  }
  grep '^PASS: ' "$work/${mode}.log" | tail -1
done
