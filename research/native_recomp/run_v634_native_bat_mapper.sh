#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || exit 2
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_perf_sprs_v29 apply_hid_state_v18 apply_fpscr_v19 apply_l2cr_v20 apply_hid4_continuous_v30 apply_bat_roots_v586 apply_bat_registers_v65 apply_hollywood_mmio_v62;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V634 source patch failed: $p";exit 1; }
done
python3 "$here/make_v634_bat_fixture.py" "$2" "$3" "$work/input"
g++ -std=c++20 -O2 -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V634 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V634 translation failed';exit 1; }
PYTHONPATH="$here" python3 - "$work/input/fixture.dol" "$work/generated" <<'PY'
import sys,re
from pathlib import Path
from prepare_v419_full_start import words_at
from prepare_v625_ipc_client import audit_native
from prepare_v591_memory_init import patch_label,MAP,RESUMES
from audit_v584_bat_translation import MAPS,audit_shards,audit_dispatch,bat_spr
from make_v634_bat_fixture import END
d=Path(sys.argv[1]).read_bytes();g=Path(sys.argv[2]);shards=sorted(g.glob('output_*.cpp'));main=(g/'main_output.cpp').read_text()
spans=[(lo,hi) for lo,hi,_ in MAPS]+[(MAP,END)]
expected={pc+4*i:(pc,w) for pc,hi in spans for i,w in enumerate(words_at(d,pc,(hi-pc)//4))}
bat={pc:(w,bat_spr(w),(w>>21)&31) for pc,(_,w) in expected.items() if bat_spr(w) is not None or w==0x4c000064}
try:
    n=audit_native((p.read_text() for p in shards),main,expected)
    a,r=audit_shards((p.read_text() for p in shards),bat);audit_dispatch(main)
    if (a,r)!=(32,3):raise ValueError('BAT coverage')
    for pc in RESUMES:
        hits=[p for p in shards if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',p.read_text())]
        if len(hits)!=1:raise ValueError('resume coverage')
        p=hits[0];p.write_text(patch_label(p.read_text(),pc,words_at(d,pc,1)[0]))
except ValueError:
    print('V634_BAT_TRANSLATION verified=0');sys.exit(1)
print(f'V634_BAT_TRANSLATION verified=1 native_words={n} writes=32 rfi=3')
PY
g++ -std=c++20 -O1 -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_bat_mapper_v634.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { echo 'V634 compile failed';exit 1; }
rc=0
ASAN_OPTIONS=abort_on_error=1:quarantine_size_mb=16 UBSAN_OPTIONS=halt_on_error=1 timeout 45s "$work/native" > "$work/run.log" 2>&1 || rc=$?
if [[ "$rc" != 0 ]];then
  grep -Ex 'V634_BAT_FAILURE (kind=exception )?trial=([0-9]|1[0-5]) stage=[0-7]( reason=[0-6] line=[0-9]{1,4})?' "$work/run.log" || true
  if grep -q 'ERROR: AddressSanitizer' "$work/run.log";then echo 'V634_BAT_SANITIZER asan=1';fi
  if grep -q 'runtime error:' "$work/run.log";then echo 'V634_BAT_SANITIZER ubsan=1';fi
  echo "V634 execution failed rc=$rc";exit 1
fi
grep -Ex 'V634_BAT_NATIVE owner=1 trials=16 returned=16 physical=32 rfi_returns=32 writes=512 modes=4 fallback=0 permissions=0 complete_image=0 boot_verified=0' "$work/run.log"
