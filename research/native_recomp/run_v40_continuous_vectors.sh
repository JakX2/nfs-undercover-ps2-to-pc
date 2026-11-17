#!/usr/bin/env bash
# Continuous Wii __start executes original Wii original OSExceptionInit fast-path prologue.
# Original owner data, translated C++ and native objects remain in mktemp only.
set -euo pipefail
if (( $#!=2 ));then
  echo 'usage: run_v40_continuous_vectors.sh NWiiRecomp_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/prerequisites.log" 2>&1 || {
  echo 'V40 needs the verified V30 HID4/HID0/SPR runtime baseline' >&2;exit 1;
}
echo 'V40_STAGE v29_runtime_verified'
# The fast continuous CI lane runs V39 first; its cache-event patch extends
# the original HID4 context anchor. Never reapply the old HID4 patch on top
# of that valid newer runtime state.
if grep -Fq 'guest_dcbf(uint32_t effective_address)' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 "$here/test_cache_continuous_patch_v39.py" "$root" > "$work/inherited-cache-guards.log" 2>&1 || {
    echo 'V40 inherited guest cache/HID4 runtime verification failed' >&2;exit 1;
  }
else
  python3 "$here/apply_hid4_continuous_v30.py" "$root" > "$work/hid4-patch.log" 2>&1 || {
    echo 'V40 HID4/FPSCR compatible native runtime patch failed' >&2;exit 1;
  }
fi
python3 "$here/test_hid4_continuous_patch_v30.py" > "$work/hid4-guards.log" 2>&1 || {
  echo 'V40 original-free HID4/FPSCR source guards failed' >&2;exit 1;
}
echo 'V40_STAGE hid4_runtime_verified'
python3 "$here/apply_cache_continuous_v39.py" "$root" > "$work/cache-patch.log" 2>&1 || {
  echo 'V40 cache-event runtime patch failed' >&2;exit 1;
}
python3 "$here/test_cache_continuous_patch_v39.py" "$root" > "$work/cache-guards.log" 2>&1 || {
  echo 'V40 cache-event source guards failed' >&2;exit 1;
}
echo 'V40_STAGE cache_patch_verified'
# Original Wii installs fifteen vectors: trace every native cache operation
# in a bounded 256-entry diagnostic buffer, not a Wii hardware cache model.
python3 "$here/apply_cache_trace_v44.py" "$root" > "$work/cache-trace-patch.log" 2>&1 || {
  echo 'V40 guest cache trace patch failed' >&2;exit 1;
}
python3 "$here/test_cache_trace_guards_v44.py" > "$work/cache-trace-guards.log" 2>&1 || {
  echo 'V40 original-free cache trace guards failed' >&2;exit 1;
}
echo 'V40_STAGE cache_trace_verified'
python3 "$here/make_start_to_vectors_v40.py" "$owner" "$work/owner-private.dol" > "$work/fixture-create.log" 2>&1 || {
  if grep -Fq 'cache helper overlaps previously translated native code' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_collision'
  elif grep -Fq 'new bounded stop overlaps previously translated PPC' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_stop_collision'
  elif grep -Fq 'owner cache helper not contained in cache-control section' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_section'
  elif grep -Eq 'call differs|callsite target changed|cache-line instruction changed|cache helper return missing' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_source'
  elif grep -Fq 'continuous startup section lacks bounded cache continuation' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_os_section'
  elif grep -Fq 'V38 test-only stop no longer matches' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_previous_stop'
  elif grep -Fq 'original Wii cache-control text section changed' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_cache_section'
  elif grep -Eq 'V38|owner-original Wii DOL|SHA-256|SHA mismatch' "$work/fixture-create.log"; then
    echo 'V40_STAGE fixture_inherited'
  else
    echo 'V40_STAGE fixture_other'
  fi
  grep -E '^V40_STAGE (inherited_fixture_ready|original_cache_calls_verified|original_cache_bodies_verified|cache_sections_mapped|cache_helpers_installed|bounded_stop_installed|os_section_verified|previous_stop_verified|cache_section_verified)$' "$work/fixture-create.log" || true
  echo 'V40 private fixture build failed; raw owner details withheld' >&2
  exit 1
}
echo 'V40_STAGE fixture_generated'
python3 "$here/test_v40_continuous_vectors_geometry.py" "$work/owner-private.dol" "$owner"
echo 'V40_STAGE geometry_verified'
# V40 cache geometry includes exact owner PPC, SHA, no-overwrite guards.
g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_vectors_v40.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator.compile.log" 2>&1 || { echo 'V40 generator compile failed' >&2; exit 1; }
echo "V40_STAGE generator_compiled"
mkdir "$work/generated"
"$work/generator" "$work/owner-private.dol" "$work/generated" owner \
  > "$work/generate.log" 2>&1 || { echo 'V40 owner source validation/code generation failed' >&2; exit 1; }
echo "V40_STAGE generation_complete"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_vectors_v40.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native.compile.log" 2>&1 || {
    echo 'V40 translated native C++ compile failed' >&2; exit 1; }
echo "V40_STAGE native_compiled"
"$work/native" "$work/owner-private.dol" owner > "$work/native.log" 2>&1 || {
  # A numeric code maps exclusively to a literal in the ORIGINAL-FREE
  # public C++ test harness. Never print the underlying private log.
  python3 "$here/classify_v40_native_failure.py" \
    "$work/native.log" "$here/test_start_to_vectors_v40.cpp" || \
    echo 'V40_NATIVE_ASSERTION id=000'
  echo 'V40 owner-original native assertion failed (private logs withheld)' >&2
  exit 1
}
echo "V40_STAGE native_test_passed"
# Only a native test that actually verified the precise callback PC can
# authorize the monotonic BOOT_PROGRESS marker for our higher startup stage.
grep -Eq '^PASS: [0-9]+ V40 recovered continuous original __start->OSExceptionInit cache loops assertions; mode=owner trials=16 stop=0x80520e58$' "$work/native.log" || {
  echo 'V40 verified checkpoint marker missing from native assertion log' >&2
  exit 1
}
echo 'PASS: genuine owner-original Wii V40 continuous __start executed original exception-cache loops'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80520E58 stage=40'
