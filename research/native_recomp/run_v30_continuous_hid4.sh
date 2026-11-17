#!/usr/bin/env bash
# Continuous Wii __start executes original HID4, speculation and FP mode.
# Original owner data, translated C++ and native objects remain in mktemp only.
set -euo pipefail
if (( $#!=2 ));then
  echo 'usage: run_v30_continuous_hid4.sh NWiiRecomp_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/prerequisites.log" 2>&1 || {
  echo 'V30 needs the verified V29/HID/L2 runtime baseline' >&2;exit 1;
}
echo 'V30_STAGE v29_runtime_verified'
python3 "$here/apply_hid4_continuous_v30.py" "$root" > "$work/hid4-patch.log" 2>&1 || {
  echo 'V30 HID4/FPSCR compatible native runtime patch failed' >&2;exit 1;
}
python3 "$here/test_hid4_continuous_patch_v30.py" > "$work/hid4-guards.log" 2>&1 || {
  echo 'V30 original-free HID4/FPSCR source guards failed' >&2;exit 1;
}
echo 'V30_STAGE hid4_patch_verified'
python3 "$here/make_start_to_hid4_v30.py" "$owner" "$work/owner-private.dol"
echo 'V30_STAGE fixture_generated'
python3 "$here/test_v30_continuous_geometry.py" "$work/owner-private.dol" "$owner"
echo 'V30_STAGE geometry_verified'
g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_hid4_v30.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator.compile.log" 2>&1 || { echo 'V30 generator compile failed' >&2; exit 1; }
echo "V30_STAGE generator_compiled"
mkdir "$work/generated"
"$work/generator" "$work/owner-private.dol" "$work/generated" owner \
  > "$work/generate.log" 2>&1 || { echo 'V30 owner source validation/code generation failed' >&2; exit 1; }
echo "V30_STAGE generation_complete"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_hid4_v30.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native.compile.log" 2>&1 || {
    echo 'V30 translated native C++ compile failed' >&2; exit 1; }
echo "V30_STAGE native_compiled"
"$work/native" "$work/owner-private.dol" owner > "$work/native.log" 2>&1 || {
  echo 'V30 owner-original native assertion failed (private logs withheld)' >&2
  exit 1
}
echo "V30_STAGE native_test_passed"
# Only a native test that actually verified the precise callback PC can
# authorize the monotonic BOOT_PROGRESS marker for our higher startup stage.
grep -Eq '^PASS: [0-9]+ V30 recovered continuous original __start->OSInit->HID4/FP init assertions; mode=owner trials=16 stop=0x80520700$' "$work/native.log" || {
  echo 'V30 verified checkpoint marker missing from native assertion log' >&2
  exit 1
}
echo 'PASS: genuine owner-original Wii V30 continuous __start HID4/speculation/FP initialization executed'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80520700 stage=30'
