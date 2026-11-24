#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_mtmsr_resume_v74 apply_hollywood_mmio_v62 apply_native_lowmem_v63 apply_hid_state_v18 apply_syscall_pc_v26 apply_cache_events_v561 apply_syscall_transfer_v461;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V651 source patch failed: $p";exit 1; }
done
python3 "$here/make_v651_open_fixture.py" "$2" "$3" "$work/input"
python3 "$here/apply_open_roots_v645.py" "$root" "$2" "$3"
python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native
python3 "$here/apply_isolated_open_cache_v651.py" "$root"
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V651 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V651 translation failed';exit 1; }
python3 "$here/make_v651_open_fixture.py" "$2" "$3" "$work/generated" --trace
python3 "$here/patch_sc_trace_v570.py" "$work/generated"
python3 "$here/patch_sc_trace_v640.py" "$work/generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --vector "$work/input/vector.bin"
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_open_request_v651.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V651 compile failed';exit 1; }
rc=0
ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$work/native" > "$work/run.log" 2>&1 || rc=$?
grep -Ex 'V651_OPEN_TRIAL n=[0-7] path=[12] request=1 serviced=0|V651_OPEN_FAILURE kind=(witness|assertion|interpreter|syscall|null_branch|mmio|mailbox|other) trial=[0-7] stage=[0-9]{1,2} open_stage=[0-9] open_reason=[0-6] reason=[0-7] line=[0-9]{1,4}' "$work/run.log" || true
[[ "$rc" == 0 ]] || { echo "V651 execution failed rc=$rc";exit 1; }
grep -Fx 'V651_OPEN_NATIVE trials=8 heap=8 request=8 rfi=8 submitted=0 serviced=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
