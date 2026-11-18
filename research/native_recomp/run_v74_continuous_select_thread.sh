#!/usr/bin/env bash
# V71: original IOS_Open to IPC submission from continuous __start.
# V40 must have installed the source-only 256-entry cache trace already.
# Owner DOL, all translated output and private failures stay in mktemp only.
set -euo pipefail
if (( $# != 2 )); then
  echo 'usage: run_v74_continuous_select_thread.sh NWII_ROOT PRIVATE_OWNER_DOL' >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "$0")" && pwd)"
owner="$(realpath "$2")"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077

python3 "$here/verify_perf_combo_v29.py" "$root" > "$work/verify-runtime.log" 2>&1 || {
  echo 'V71 inherited performance/HID4 runtime invalid' >&2; exit 1;
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
print("PASS: V71 reused verified V40 256-entry guest cache trace and emitter")
PY
g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_exi_id_device_v56.cpp" -o "$work/exi-device-test"
"$work/exi-device-test"
python3 "$here/test_jump_table_patch_v58.py"
g++ -std=c++20 -O2 -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" \
  "$here/test_jump_table_analyzer_v58.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  -o "$work/jump-table-test" > "$work/jump-table-compile.log" 2>&1 || {
    echo 'V72 original-free jump-table analyzer test compile failed' >&2; exit 1;
  }
"$work/jump-table-test"
python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native
g++ -std=c++20 -O2 -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" \
  "$here/test_explicit_tail_roots_v71.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  -o "$work/tail-root-test" > "$work/tail-root-compile.log" 2>&1 || {
    echo 'V72 original-free tail-root analyzer compile failed' >&2; exit 1;
  }
"$work/tail-root-test"
g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_exi_sram_device_v60.cpp" -o "$work/sram-device-test"
"$work/sram-device-test"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -I"$root/nWiiRuntime/include" \
  "$here/test_hollywood_mmio_v62.cpp" -o "$work/hollywood-mmio-test"
"$work/hollywood-mmio-test"
g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_native_sc_vector_v63.cpp" -o "$work/sc-vector-test"
"$work/sc-vector-test"
python3 "$here/test_native_lowmem_patch_v63.py"
g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_dsp_boot_device_v64.cpp" -o "$work/dsp-device-test"
"$work/dsp-device-test"
g++ -std=c++20 -O2 -Wall -Wextra -Werror -I"$root/nWiiRuntime/include" "$here/test_bat_registers_v65.cpp" -o "$work/bat-test"
"$work/bat-test"
python3 "$here/test_dcbz_patch_v67.py"
g++ -std=c++20 -O2 -Wall -Wextra -Werror "$here/test_flat_cacheline_zero_v67.cpp" -o "$work/dcbz-test"
"$work/dcbz-test"
echo 'V74_STAGE runtime_cache_trace_verified'

python3 "$here/make_start_to_select_thread_v74.py" "$owner" "$work/private.dol"   > "$work/build-private.log" 2>&1 || {
    python3 "$here/classify_v74_fixture_failure.py" "$work/build-private.log" || true
    echo 'V71 fixture construction failed; owner details withheld' >&2; exit 1;
  }
echo 'V74_STAGE fixture_generated'
python3 "$here/test_v74_continuous_select_thread_geometry.py" "$work/private.dol" "$owner"   > "$work/private-geometry.log" 2>&1 || {
    echo 'V71 STM geometry guard failed' >&2; exit 1;
  }
echo 'V74_STAGE geometry_verified'

g++ -std=c++20 -O2 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/generate_start_to_select_thread_v74.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" \
  > "$work/generator-compile.log" 2>&1 || {
    python3 "$here/classify_v67_compile_failure.py" "$work/generator-compile.log"
    echo 'V73 generator compilation failed; details withheld' >&2; exit 1;
  }
echo 'V74_STAGE generator_compiled'
mkdir "$work/generated"
"$work/generator" "$work/private.dol" "$work/generated" owner   > "$work/generation.log" 2>&1 || {
    python3 "$here/classify_v67_generator_failure.py" "$work/generation.log" "$here/generate_start_to_select_thread_v74.cpp"
    echo 'V72 original PPC generator guards failed; details withheld' >&2; exit 1;
  }
echo 'V74_STAGE generation_complete'
# Compile public harness and private generated source independently to
# classify warnings without ever showing private source or diagnostics.
for unit in harness generated loader; do
  case "$unit" in
    harness) source="$here/test_start_to_select_thread_v74.cpp";;
    generated) source="$work/generated/output.cpp";;
    loader) source="$root/nWiiRuntime/src/core/loader.cpp";;
  esac
  g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
    -I"$root/nWiiRuntime/include" -c "$source" -o "$work/$unit.o" > "$work/native-compile.log" 2>&1 || {
      python3 "$here/classify_v74_compile_failure.py" "$work/native-compile.log" "$unit"
      exit 1
    }
done
g++ "$work/harness.o" "$work/generated.o" "$work/loader.o" \
  -o "$work/native" > "$work/native-compile.log" 2>&1 || {
    python3 "$here/classify_v71_link_failure.py" "$work/native-compile.log"
    echo 'V72 original translated native compilation failed' >&2; exit 1;
  }
echo 'V74_STAGE native_compiled'
"$work/native" "$work/private.dol" owner "$owner" > "$work/private-native.log" 2>&1 || {
  python3 "$here/classify_v67_native_failure.py" \
    "$work/private-native.log" "$here/test_start_to_select_thread_v74.cpp" || \
    echo 'V71_NATIVE_ASSERTION id=000'
  echo 'V72 original IOS_Open assertion failed; details withheld' >&2
  grep -E '^V74_IRQ_ENTRY idle=1 waiting=1 vector=1 srr=1 ack=1$' "$work/private-native.log" | sort -u || true
  grep -E '^V73_WAIT_STATE waiting=[01] head=[01] tail=[01] queue=[01] links=[01] force0=[01]$' "$work/private-native.log" | sort -u || true
  grep -E '^V72_IRQ_HANDLER candidate=[123]$' "$work/private-native.log" | sort -u || true
  grep -E '^V72_SDA phase=[01] site=[0-9a-f]{8} addr=[0-9a-f]{8} width=[124] init=[01] initial_nz=[01] live_nz=[01] equal=[01]$' "$work/private-native.log" | sort -u || true
  grep -E '^V72_SEND_STATE lr=[01] msg=[0-9]{1,2} x1=[0-9]{1,2} ee=[01] flush=[0-9]{1,2} disable=[0-9]{1,2} ack=[0-9]{1,2}$' "$work/private-native.log" || true
  grep -E '^V71_REQUEST_SHAPE request=[0-9]{1,3} command=[0-9]{1,3} path=[0-9]{1,3}$' "$work/private-native.log" || true
  exit 1
}
echo 'V74_STAGE native_test_passed'
grep -E '^V74_IRQ_ENTRY idle=1 waiting=1 vector=1 srr=1 ack=1$' "$work/private-native.log" | sort -u
grep -E '^V73_WAIT_STATE waiting=[01] head=[01] tail=[01] queue=[01] links=[01] force0=[01]$' "$work/private-native.log" | sort -u
grep -E '^V72_IRQ_HANDLER candidate=[123]$' "$work/private-native.log" | sort -u
grep -E '^V71_REQUEST_SHAPE request=[0-9]{1,3} command=[0-9]{1,3} path=[0-9]{1,3}$' "$work/private-native.log" | sort -u
grep -Eq '^PASS: [0-9]+ V74 recovered continuous original __start->external-IRQ entry assertions; mode=owner trials=16 stop=0x80000500$' \
  "$work/private-native.log" || {
  echo 'V73 original native return checkpoint marker is missing' >&2; exit 1;
}
echo 'PASS: original Wii continuous __start executed original scheduler until external IRQ entry at 0x80000500'
echo 'BOOT_PROGRESS entry=0x8000403C pc=0x80000500 stage=74'
