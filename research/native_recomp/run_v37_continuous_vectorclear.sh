#!/usr/bin/env bash
# Continuous Wii __start executes original Wii original OSExceptionInit fast-path prologue.
# Original owner data, translated C++ and native objects remain in mktemp only.
set -euo pipefail
if (( $#!=2 ));then
  echo 'usage: run_v37_continuous_vectorclear.sh NWiiRecomp_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/prerequisites.log" 2>&1 || {
  echo 'V37 needs the verified V30 HID4/HID0/SPR runtime baseline' >&2;exit 1;
}
echo 'V37_STAGE v29_runtime_verified'
python3 "$here/apply_hid4_continuous_v30.py" "$root" > "$work/hid4-patch.log" 2>&1 || {
  echo 'V37 HID4/FPSCR compatible native runtime patch failed' >&2;exit 1;
}
python3 "$here/test_hid4_continuous_patch_v30.py" > "$work/hid4-guards.log" 2>&1 || {
  echo 'V37 original-free HID4/FPSCR source guards failed' >&2;exit 1;
}
echo 'V37_STAGE hid4_runtime_verified'
python3 "$here/make_start_to_vectorclear_v37.py" "$owner" "$work/owner-private.dol"
echo 'V37_STAGE fixture_generated'
python3 "$here/test_v37_continuous_vectorclear_geometry.py" "$work/owner-private.dol" "$owner"
echo 'V37_STAGE geometry_verified'
python3 "$here/test_v37_negative_guards.py" "$work/owner-private.dol" "$owner" \
  > "$work/negative-guards.log" 2>&1 || {
  echo 'V37 private code-mutation/integrity guards failed' >&2; exit 1;
}
echo 'V37_STAGE negative_guards_verified'
g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_vectorclear_v37.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator.compile.log" 2>&1 || { echo 'V37 generator compile failed' >&2; exit 1; }
echo "V37_STAGE generator_compiled"
mkdir "$work/generated"
"$work/generator" "$work/owner-private.dol" "$work/generated" owner \
  > "$work/generate.log" 2>&1 || { echo 'V37 owner source validation/code generation failed' >&2; exit 1; }
echo "V37_STAGE generation_complete"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_vectorclear_v37.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native.compile.log" 2>&1 || {
    echo 'V37 translated native C++ compile failed' >&2; exit 1; }
echo "V37_STAGE native_compiled"
"$work/native" "$work/owner-private.dol" owner > "$work/native.log" 2>&1 || {
  # A numeric code maps exclusively to a literal in the ORIGINAL-FREE
  # public C++ test harness. Never print the underlying private log.
  python3 "$here/classify_v37_native_failure.py" \
    "$work/native.log" "$here/test_start_to_vectorclear_v37.cpp" || \
    echo 'V37_NATIVE_ASSERTION id=000'
  echo 'V37 owner-original native assertion failed (private logs withheld)' >&2
  exit 1
}
echo "V37_STAGE native_test_passed"
# Only a native test that actually verified the precise callback PC can
# authorize the monotonic BOOT_PROGRESS marker for our higher startup stage.
grep -Eq '^PASS: [0-9]+ V37 recovered continuous original __start->OSExceptionInit vector-template clearing assertions; mode=owner trials=16 stop=0x80520d80$' "$work/native.log" || {
  echo 'V37 verified checkpoint marker missing from native assertion log' >&2
  exit 1
}
echo 'PASS: genuine owner-original Wii V37 continuous __start executed original exception-template clearing'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80520D80 stage=37'
