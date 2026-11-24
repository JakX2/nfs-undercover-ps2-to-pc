#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_mtmsr_resume_v74 apply_hollywood_mmio_v62;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V626 source patch failed: $p";exit 1; }
done
python3 "$here/make_v626_ipc_fixture.py" "$2" "$3" "$work/input"
g++ -std=c++20 -O2 -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V626 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V626 translation failed';exit 1; }
# Verify native coverage of the ten client spans (helpers are exercised by
# the exact witness and forbidden interpreter hooks).
PYTHONPATH="$here" python3 - "$work/input/fixture.dol" "$work/generated" <<'PY'
import sys
from pathlib import Path
from prepare_v625_ipc_client import audit_native
from make_v624_ipc_geometry import SPANS
from prepare_v419_full_start import words_at
dol=Path(sys.argv[1]).read_bytes();root=Path(sys.argv[2])
expected={pc+4*i:(pc,w) for pc,n in SPANS for i,w in enumerate(words_at(dol,pc,n//4))}
try:n=audit_native((p.read_text() for p in root.glob('output_*.cpp')),(root/'main_output.cpp').read_text(),expected)
except ValueError:print('V626_IPC_TRANSLATION verified=0');sys.exit(1)
print(f'V626_IPC_TRANSLATION verified=1 native_words={n}')
PY
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_ipc_client_v626.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V626 compile failed';exit 1; }
rc=0
ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$work/native" > "$work/run.log" 2>&1 || rc=$?
if [[ "$rc" != 0 ]]; then
  grep -Ex 'V627_IPC_FAILURE kind=(witness|assertion|interpreter|syscall|null_branch|mmio|mailbox|other) trial=[0-7] stage=([0-9]|1[0-9]) reason=[0-7] line=[0-9]{1,4}' "$work/run.log" || true
  if grep -q 'ERROR: AddressSanitizer' "$work/run.log"; then echo 'V627_IPC_SANITIZER asan=1';fi
  if grep -q 'runtime error:' "$work/run.log"; then echo 'V627_IPC_SANITIZER ubsan=1';fi
  echo "V626 execution failed rc=$rc";exit 1
fi
grep -Ex 'V627_IPC_POLLS restore=16 backward=[0-9]{1,4}' "$work/run.log"
grep -Ex 'V626_IPC_NATIVE owner=1 trials=8 returned=8 calls=136 callbacks=16 mailbox=8 fallback=0 actual_ios=0 complete_image=0 boot_verified=0' "$work/run.log"
