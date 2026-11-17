#!/usr/bin/env bash
# V56: execute the original uncached EXIGetID immediate transaction from continuous __start.
# V40 must have installed the source-only 256-entry cache trace already.
# Owner DOL, all translated output and private failures stay in mktemp only.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: run_v56_continuous_exi_transaction.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077

python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/verify-runtime.log" 2>&1 || {
  echo 'V56 inherited performance/HID4 runtime invalid' >&2; exit 1;
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
print("PASS: V56 reused verified V40 256-entry guest cache trace and emitter")
PY
g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_exi_id_device_v56.cpp" -o "$work/exi-device-test"
"$work/exi-device-test"
echo 'V56_STAGE runtime_cache_trace_verified'

python3 "$here/make_start_to_exi_transaction_v56.py" "$owner" "$work/private.dol"   > "$work/build-private.log" 2>&1 || {
    echo 'V56 fixture construction failed; owner details withheld' >&2; exit 1;
  }
echo 'V56_STAGE fixture_generated'
python3 "$here/test_v56_continuous_exi_transaction_geometry.py" "$work/private.dol" "$owner"   > "$work/private-geometry.log" 2>&1 || {
    echo 'V56 EXIGetID cached fast-path geometry guard failed' >&2; exit 1;
  }
echo 'V56_STAGE geometry_verified'

g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_exi_transaction_v56.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator-compile.log" 2>&1 || {
    echo 'V56 generator compilation failed; details withheld' >&2; exit 1;
  }
echo 'V56_STAGE generator_compiled'
mkdir "$work/generated"
"$work/generator" "$work/private.dol" "$work/generated" owner   > "$work/generation.log" 2>&1 || {
    echo 'V56 original PPC generator guards failed; details withheld' >&2; exit 1;
  }
echo 'V56_STAGE generation_complete'
g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_start_to_exi_transaction_v56.cpp" "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  -o "$work/native" > "$work/native-compile.log" 2>&1 || {
    echo 'V56 original translated native compilation failed' >&2; exit 1;
  }
echo 'V56_STAGE native_compiled'
"$work/native" "$work/private.dol" owner > "$work/private-native.log" 2>&1 || {
  python3 "$here/classify_v56_native_failure.py" \
    "$work/private-native.log" "$here/test_start_to_exi_transaction_v56.cpp" || \
    echo 'V56_NATIVE_ASSERTION id=000'
  echo 'V56 original native EXI assertion failed; details withheld' >&2
  exit 1
}
echo 'V56_STAGE native_test_passed'
grep -Eq '^PASS: [0-9]+ V56 recovered continuous original __start->OSInit EXI-transaction assertions; mode=owner trials=16 stop=0x804efab4$' \
  "$work/private-native.log" || {
  echo 'V56 original native return checkpoint marker is missing' >&2; exit 1;
}
echo 'PASS: original Wii continuous __start returned from original uncached EXIGetID transaction at 0x804EFAB4'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x804EFAB4 stage=56'
