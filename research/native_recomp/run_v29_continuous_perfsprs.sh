#!/usr/bin/env bash
# Continuous Wii __start executes original MMCR0/MMCR1 and six performance SPR helpers.
# Original owner data, translated C++ and native objects remain in mktemp only.
set -euo pipefail
if (( $#!=2 ));then
  echo 'usage: run_v29_continuous_perfsprs.sh NWiiRecomp_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
if ! grep -q 'uint32_t l2cr = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h";then
  python3 "$here/apply_hid_state_v18.py" "$root"
  python3 "$here/apply_fpscr_v19.py" "$root"
fi
python3 "$here/apply_l2cr_v20.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/apply_perf_sprs_v29.py" "$root" > "$work/perf-patch.log" 2>&1 || {
  echo 'V29 performance SPR source-only runtime patch failed' >&2; exit 1;
}
python3 "$here/test_perf_patch_guards_v29.py" "$root" > "$work/perf-guards.log" 2>&1 || {
  echo 'V29 original-free performance SPR guard checks failed' >&2; exit 1;
}
python3 "$here/make_start_to_perfsprs_v29.py" "$owner" "$work/owner-private.dol"
python3 "$here/test_v29_perfsprs_geometry.py" "$work/owner-private.dol" "$owner"
g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_perfsprs_v29.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator.compile.log" 2>&1 || { echo 'V29 generator compile failed' >&2; exit 1; }
mkdir "$work/generated"
"$work/generator" "$work/owner-private.dol" "$work/generated" owner \
  > "$work/generate.log" 2>&1 || { echo 'V29 owner source validation/code generation failed' >&2; exit 1; }
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_perfsprs_v29.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native.compile.log" 2>&1 || {
    echo 'V29 translated native C++ compile failed' >&2; exit 1; }
"$work/native" "$work/owner-private.dol" owner > "$work/native.log" 2>&1 || {
  echo 'V29 owner-original native assertion failed (private logs withheld)' >&2
  exit 1
}
# Only a native test that actually verified the precise callback PC can
# authorize the monotonic BOOT_PROGRESS marker for our higher startup stage.
grep -Eq '^PASS: [0-9]+ V29 recovered continuous original __start->OSInit->performance SPR init assertions; mode=owner trials=16 stop=0x805206f0$' "$work/native.log" || {
  echo 'V29 verified checkpoint marker missing from native assertion log' >&2
  exit 1
}
echo 'PASS: genuine owner-original Wii V29 continuous __start performance SPR writes executed'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805206F0 stage=29'
