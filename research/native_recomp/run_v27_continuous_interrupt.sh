#!/usr/bin/env bash
# The next authentic continuous Wii startup call, executed from original __start.
# Original owner data, translated C++ and native objects remain in mktemp only.
set -euo pipefail
if (( $#!=2 ));then
  echo 'usage: run_v27_continuous_interrupt.sh NWiiRecomp_ROOT PRIVATE_OWNER_DOL' >&2
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
python3 "$here/make_start_to_interrupt_v27.py" "$owner" "$work/owner-private.dol"
python3 "$here/test_v27_interrupt_geometry.py" "$work/owner-private.dol" "$owner"
g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_interrupt_v27.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator.compile.log" 2>&1 || { echo 'V27 generator compile failed' >&2; exit 1; }
mkdir "$work/generated"
"$work/generator" "$work/owner-private.dol" "$work/generated" owner \
  > "$work/generate.log" 2>&1 || { echo 'V27 owner source validation/code generation failed' >&2; exit 1; }
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_interrupt_v27.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native.compile.log" 2>&1 || {
    echo 'V27 translated native C++ compile failed' >&2; exit 1; }
"$work/native" "$work/owner-private.dol" owner > "$work/native.log" 2>&1 || {
  echo 'V27 owner-original native assertion failed (private logs withheld)' >&2
  exit 1
}
# Only a native test that actually verified the precise callback PC can
# authorize the monotonic BOOT_PROGRESS marker for our higher startup stage.
grep -Eq '^PASS: [0-9]+ V27 recovered continuous original __start->OSInit->posttime interrupt call assertions; mode=owner trials=16 stop=0x805206bc$' "$work/native.log" || {
  echo 'V27 verified checkpoint marker missing from native assertion log' >&2
  exit 1
}
echo 'PASS: genuine owner-original Wii V27 continuous __start interrupt call executed'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805206BC stage=27'
