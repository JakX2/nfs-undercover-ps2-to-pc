#!/usr/bin/env bash
# V42: execute the authentic original Wii syscall initializer from __start.
# V40 must have installed the source-only 256-entry cache trace already.
# Owner DOL, all translated output and private failures stay in mktemp only.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: run_v42_continuous_epilogue.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077

python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/verify-runtime.log" 2>&1 || {
  echo 'V42 inherited performance/HID4 runtime invalid' >&2; exit 1;
}
python3 - "$root" "$here" > "$work/verify-cache.log" 2>&1 <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from apply_cache_events_v43 import EMIT_AFTER,ISYNC_AFTER,EMITTER
from apply_cache_trace_v44 import NEW,FILE
root=Path(sys.argv[1])
ctx=(root/FILE).read_text(encoding="utf-8")
emit=(root/EMITTER).read_text(encoding="utf-8")
assert all(ctx.count(anchor)==1 for anchor in NEW)
assert all(ctx.count(anchor)==0 for anchor in (
    "std::array<uint32_t, 32> guest_flush_lines{};",
    "std::array<uint32_t, 32> guest_invalidate_lines{};"))
assert emit.count(EMIT_AFTER)==1 and emit.count(ISYNC_AFTER)==1
print("PASS: V42 reused verified V40 256-entry guest cache trace and emitter")
PY
echo 'V42_STAGE runtime_cache_trace_verified'

python3 "$here/make_start_to_syscall_v42.py" "$owner" "$work/private.dol"   > "$work/build-private.log" 2>&1 || {
    echo 'V42 fixture construction failed; owner details withheld' >&2; exit 1;
  }
echo 'V42_STAGE fixture_generated'
python3 "$here/test_v42_continuous_syscall_geometry.py" "$work/private.dol" "$owner"   > "$work/private-geometry.log" 2>&1 || {
    echo 'V42 original syscall vector or no-overwrite guard failed' >&2; exit 1;
  }
echo 'V42_STAGE geometry_verified'

g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_syscall_v42.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator-compile.log" 2>&1 || {
    echo 'V42 generator compilation failed; details withheld' >&2; exit 1;
  }
echo 'V42_STAGE generator_compiled'
mkdir "$work/generated"
"$work/generator" "$work/private.dol" "$work/generated" owner   > "$work/generation.log" 2>&1 || {
    echo 'V42 original PPC generator guards failed; details withheld' >&2; exit 1;
  }
echo 'V42_STAGE generation_complete'
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_syscall_v42.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native-compile.log" 2>&1 || {
    echo 'V42 original translated native compilation failed' >&2; exit 1;
  }
echo 'V42_STAGE native_compiled'
"$work/native" "$work/private.dol" owner > "$work/private-native.log" 2>&1 || {
  python3 "$here/classify_v42_native_failure.py" \
    "$work/private-native.log" "$here/test_start_to_syscall_v42.cpp" || \
    echo 'V42_NATIVE_ASSERTION id=000'
  echo 'V42 original native syscall-vector assertion failed; details withheld' >&2
  exit 1
}
echo 'V42_STAGE native_test_passed'
grep -Eq '^PASS: [0-9]+ V42 recovered continuous original __start->OSInit syscall-vector assertions; mode=owner trials=16 stop=0x805208b0$' \
  "$work/private-native.log" || {
  echo 'V42 original native return checkpoint marker is missing' >&2; exit 1;
}
echo 'PASS: original Wii continuous __start executed native __OSInitSystemCall syscall-vector installation'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x805208B0 stage=42'
