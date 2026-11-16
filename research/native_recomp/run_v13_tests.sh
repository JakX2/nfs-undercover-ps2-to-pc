#!/usr/bin/env bash
# Build using a private upstream NWiiRecomp checkout. Run from toolkit directory.
set -euo pipefail
if (( $# != 1 && $# != 4 )); then
 echo "Usage: $0 NWII_SOURCE_ROOT [OWNER_DOL NIBBLE_HEX COPY_HEX]" >&2; exit 2
fi
root="$(cd "$1" && pwd)"
source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
# Upstream analyzer/recompiler has pre-existing unused-variable/sign-compare
# warnings; keep warnings enabled, but enforce -Werror only on generated leaf
# tests (except upstream-generated entry labels, which may be unused).
compile=(${CXX:-g++} -std=c++20 -O1 -Wall -Wextra -Wno-unused-label "${inc[@]}")
strict=(${CXX:-g++} -std=c++20 -O2 -Wall -Wextra -Werror -Wno-unused-label "${inc[@]}")
"${compile[@]}" "$source_dir/recompile_leaf_v13.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/recompile_leaf_v13"
python3 "$source_dir/make_synthetic_dol_v13.py" "$work/synthetic.dol"
python3 "$source_dir/test_leaf_driver_v13.py" "$work/recompile_leaf_v13" "$work/synthetic.dol" "$work"
"$work/recompile_leaf_v13" "$work/synthetic.dol" 80004000 8 v13_guest_add "$work/private_generated_add.cpp"
"$work/recompile_leaf_v13" "$work/synthetic.dol" 80004008 12 v13_guest_store "$work/private_generated_store.cpp"
# Reject an incomplete leaf (the same mistake caught on the real DOL initially).
if "$work/recompile_leaf_v13" "$work/synthetic.dol" 80004000 4 v13_guest_bad "$work/bad.cpp"; then
 echo 'ERROR: incomplete leaf unexpectedly accepted' >&2; exit 1
fi
if test -e "$work/bad.cpp"; then echo 'ERROR: invalid input wrote output file' >&2; exit 1; fi
"${strict[@]}" "$source_dir/test_synthetic_leaf_v13.cpp" \
 "$work/private_generated_add.cpp" "$work/private_generated_store.cpp" \
 -o "$work/test_synthetic_leaf_v13"
"$work/test_synthetic_leaf_v13"
if (( $# == 4 )); then
  "$work/recompile_leaf_v13" "$2" "$3" 28 v13_guest_nibble "$work/private_generated_nibble.cpp"
  "$work/recompile_leaf_v13" "$2" "$4" 44 v13_guest_copy "$work/private_generated_copy.cpp"
  "${strict[@]}" "$source_dir/test_real_leaf_v13.cpp" \
    "$work/private_generated_nibble.cpp" "$work/private_generated_copy.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/test_real_leaf_v13"
  "$work/test_real_leaf_v13" "$2" "$3" "$4"
fi
