#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_mtmsr_resume_v74 apply_hollywood_mmio_v62 apply_native_lowmem_v63 apply_hid_state_v18 apply_syscall_pc_v26 apply_cache_events_v561 apply_syscall_transfer_v461;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V1251 source patch failed: $p";exit 1; }
done
python3 "$here/make_v1245_open_fixture.py" "$2" "$3" "$work/input"
python3 "$here/apply_open_roots_v645.py" "$root" "$2" "$3"
python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native
python3 "$here/apply_isolated_open_cache_v651.py" "$root"
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V1251 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V1251 translation failed';exit 1; }
python3 "$here/make_v651_open_fixture.py" "$2" "$3" "$work/generated" --trace
PYTHONPATH="$here" python3 - "$work/input/fixture.dol" "$work/generated" <<'PY'
import sys
from pathlib import Path
from prepare_v625_ipc_client import audit_native
from make_v624_ipc_geometry import SPANS
from prepare_v629_stm_open import STM
from prepare_v419_full_start import words_at
d=Path(sys.argv[1]).read_bytes();root=Path(sys.argv[2])
expected={pc+4*i:(pc,w) for pc,n in SPANS for i,w in enumerate(words_at(d,pc,n//4))}
expected.update({STM+4*i:(STM,w) for i,w in enumerate(words_at(d,STM,23))})
try:n=audit_native((p.read_text() for p in root.glob('output_*.cpp')),(root/'main_output.cpp').read_text(),expected)
except ValueError:print('V1251_IPC_STM_TRANSLATION verified=0');sys.exit(1)
print(f'V1251_IPC_STM_TRANSLATION verified=1 native_words={n}')
PY
python3 "$here/patch_sc_trace_v570.py" "$work/generated"
python3 "$here/patch_sc_trace_v640.py" "$work/generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --vector "$work/input/vector.bin"
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_submit_join_v1251.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { python3 "$here/classify_open_compile_v654.py" "$work/compile.log";echo 'V1251 compile failed';exit 1; }
rc=0
ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$work/native" > "$work/run.log" 2>&1 || rc=$?
grep -Ex 'V1254_SUBMIT_MMIO_REFUSAL category=[1-5] writes=[0-2] control=[01] low_bits=[0-9]{1,2} prior=[0-9]{1,2}|V1251_OPEN_TRIAL n=[0-7] path=[12] request=1 native_rfi=1 serviced=0|V1251_SUBMIT_TRIAL n=[0-7] path=[12] ack=1 reply=0 si_quiescent=1|V1251_OPEN_FAILURE kind=(witness|assertion|interpreter|syscall|null_branch|mmio|mailbox|other) trial=[0-7] stage=[0-9]{1,2} reason=[0-7] line=[0-9]{1,4}' "$work/run.log" || true
[[ "$rc" == 0 ]] || { echo "V1251 execution failed rc=$rc";exit 1; }
grep -Fx 'V1251_SUBMIT_NATIVE owner=1 trials=8 ipc_returned=8 stm_entry=8 request=8 submitted=8 ack=8 reply=0 native_rfi=16 si_quiescent=8 synthetic_ack=1 synthetic_caller=1 synthetic_bridge=1 seeded_vector=1 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
