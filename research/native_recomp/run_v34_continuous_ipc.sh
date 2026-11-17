#!/usr/bin/env bash
# Continuous Wii __start executes original Wii original __OSInitIPCBuffer helper.
# Original owner data, translated C++ and native objects remain in mktemp only.
set -euo pipefail
if (( $#!=2 ));then
  echo 'usage: run_v34_continuous_ipc.sh NWiiRecomp_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/prerequisites.log" 2>&1 || {
  echo 'V34 needs the verified V30 HID4/HID0/SPR runtime baseline' >&2;exit 1;
}
echo 'V34_STAGE v29_runtime_verified'
python3 "$here/apply_hid4_continuous_v30.py" "$root" > "$work/hid4-patch.log" 2>&1 || {
  echo 'V34 HID4/FPSCR compatible native runtime patch failed' >&2;exit 1;
}
python3 "$here/test_hid4_continuous_patch_v30.py" > "$work/hid4-guards.log" 2>&1 || {
  echo 'V34 original-free HID4/FPSCR source guards failed' >&2;exit 1;
}
echo 'V34_STAGE hid4_runtime_verified'
python3 "$here/make_start_to_ipc_v34.py" "$owner" "$work/owner-private.dol"
echo 'V34_STAGE fixture_generated'
python3 "$here/test_v34_continuous_ipc_geometry.py" "$work/owner-private.dol" "$owner"
echo 'V34_STAGE geometry_verified'
g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_ipc_v34.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator.compile.log" 2>&1 || { echo 'V34 generator compile failed' >&2; exit 1; }
echo "V34_STAGE generator_compiled"
mkdir "$work/generated"
"$work/generator" "$work/owner-private.dol" "$work/generated" owner \
  > "$work/generate.log" 2>&1 || { echo 'V34 owner source validation/code generation failed' >&2; exit 1; }
echo "V34_STAGE generation_complete"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_ipc_v34.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native.compile.log" 2>&1 || {
    echo 'V34 translated native C++ compile failed' >&2; exit 1; }
echo "V34_STAGE native_compiled"
"$work/native" "$work/owner-private.dol" owner > "$work/native.log" 2>&1 || {
  echo 'V34 owner-original native assertion failed (private logs withheld)' >&2
  exit 1
}
echo "V34_STAGE native_test_passed"
# Only a native test that actually verified the precise callback PC can
# authorize the monotonic BOOT_PROGRESS marker for our higher startup stage.
grep -Eq '^PASS: [0-9]+ V34 recovered continuous original __start->OSInit->IPC buffer init assertions; mode=owner trials=16 stop=0x805208a8$' "$work/native.log" || {
  echo 'V34 verified checkpoint marker missing from native assertion log' >&2
  exit 1
}
echo 'PASS: genuine owner-original Wii V34 continuous __start original IPC-buffer pointer initialization executed'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805208A8 stage=34'
