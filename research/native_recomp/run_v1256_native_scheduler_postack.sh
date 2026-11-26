#!/usr/bin/env bash
set -euo pipefail
reply_entry_mode=0;reply_body_mode=0
if [[ $# == 4 && "$4" == --irq-reply-wake-entry ]];then
  reply_body_mode=1
  set -- "$1" "$2" "$3" --irq-reply-entry
fi
if [[ $# == 4 && "$4" == --irq-reply-entry ]];then
  reply_entry_mode=1
  set -- "$1" "$2" "$3" --irq-return
fi
[[ $# == 3 || ( $# == 4 && ( "$4" == --irq-entry || "$4" == --irq-vector || "$4" == --irq-dispatch || "$4" == --irq-ack || "$4" == --irq-return ) ) ]] || exit 2
extra=();overlays=()
if [[ $# == 4 ]];then extra=(-DUNDERCOVER_V1259_IRQ_ENTRY);fi
if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1260_IRQ_VECTOR);overlays+=(--native-external-overlay-preflight);fi
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1261_IPC_DISPATCH);fi
if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1266_JOINED_ACK);fi
if [[ "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1271_IPC_RETURN);fi
if [[ "$reply_entry_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1275_REPLY_ENTRY);fi
if [[ "$reply_body_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1282_REPLY_WAKE);fi
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_mtmsr_resume_v74 apply_hollywood_mmio_v62 apply_native_lowmem_v63 apply_hid_state_v18 apply_syscall_pc_v26 apply_cache_events_v561 apply_syscall_transfer_v461;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V1256 source patch failed: $p";exit 1; }
done
if [[ "$reply_body_mode" == 1 ]];then python3 "$here/apply_isolated_dcbi_v1276.py" "$root";fi
python3 "$here/make_v1256_scheduler_fixture.py" "$2" "$3" "$work/input"
if [[ $# == 4 ]];then python3 "$here/prepare_v1259_scheduler_vector.py" "$2" "$3" "$work/input/v1259_private_vector.h";fi
if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  python3 "$here/apply_exception_sprg.py" "$root" > "$work/patch.log" 2>&1 || { echo 'V1260 SPRG patch failed';exit 1; }
  python3 "$here/prepare_v1260_scheduler_vector.py" "$2" "$3" "$work/input"
fi
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1261_ipc_dispatch.py" "$2" "$3" "$work/input";fi
if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1266_joined_ack.py" "$2" "$3" "$work/input";fi
if [[ "${4-}" == --irq-return ]];then python3 "$here/prepare_v1270_ipc_epilogue.py" "$2" "$3" "$work/input";fi
if [[ "$reply_body_mode" == 1 ]];then python3 "$here/prepare_v1281_reply_fixture.py" "$2" "$3" "$work/input";fi
python3 "$here/apply_open_roots_v645.py" "$root" "$2" "$3"
if [[ "${4-}" != --irq-return ]];then python3 "$here/make_v1256_scheduler_fixture.py" "$2" "$3" "$work/input" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp";fi
if [[ "${4-}" == --irq-vector ]];then python3 "$here/prepare_v1260_scheduler_vector.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer;fi
if [[ "${4-}" == --irq-dispatch ]];then python3 "$here/prepare_v1261_ipc_dispatch.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer;fi
if [[ "${4-}" == --irq-ack ]];then python3 "$here/prepare_v1266_joined_ack.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer;fi
if [[ "$reply_body_mode" == 1 ]];then
  python3 "$here/prepare_v1281_reply_fixture.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "${4-}" == --irq-return ]];then
  python3 "$here/prepare_v1270_ipc_epilogue.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer
fi
python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native
python3 "$here/apply_isolated_open_cache_v651.py" "$root"
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V1256 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay "${overlays[@]}" --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V1256 translation failed';exit 1; }
python3 "$here/make_v651_open_fixture.py" "$2" "$3" "$work/generated" --trace
PYTHONPATH="$here" python3 - "$work/input/fixture.dol" "$work/generated" <<'PY'
import sys
from pathlib import Path
from prepare_v625_ipc_client import audit_native
from make_v624_ipc_geometry import SPANS
from prepare_v629_stm_open import STM
from make_v1252_sleep_fixture import SLEEP,SELECT,SIZE
from make_v1256_scheduler_fixture import ALLOWED,FORBIDDEN
from prepare_v680_si_helper import verify_direct
from make_start_to_select_thread_v74 import EDGES
from prepare_v419_full_start import words_at
d=Path(sys.argv[1]).read_bytes();root=Path(sys.argv[2])
expected={pc+4*i:(pc,w) for pc,n in SPANS for i,w in enumerate(words_at(d,pc,n//4))}
expected.update({STM+4*i:(STM,w) for i,w in enumerate(words_at(d,STM,23))})
expected.update({SLEEP+4*i:(SLEEP,w) for i,w in enumerate(words_at(d,SLEEP,SIZE//4))})
sizes={int(a,16):int(n) for _,a,n in (row.split(',') for row in (root.parent/'input/symbols.csv').read_text().splitlines()[1:])}
for pc in (*ALLOWED,*FORBIDDEN):
    expected.update({pc+4*i:(pc,w) for i,w in enumerate(words_at(d,pc,1 if pc in FORBIDDEN else sizes[pc]//4))})
shards=[p.read_text() for p in root.glob('output_*.cpp')]
for site,target in EDGES:
    owners=[s for s in shards if f'loc_{site:X}: ;' in s]
    if len(owners)!=1:sys.exit('V1256 scheduler direct owner refused')
    try:verify_direct(owners[0],site,target)
    except ValueError:sys.exit('V1256 scheduler direct edge refused')
try:n=audit_native((p.read_text() for p in root.glob('output_*.cpp')),(root/'main_output.cpp').read_text(),expected)
except ValueError:print('V1256_IPC_STM_TRANSLATION verified=0');sys.exit(1)
print(f'V1256_IPC_STM_TRANSLATION verified=1 native_words={n}')
PY
if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1260_scheduler_vector.py" "$2" "$3" "$work/generated" --install;fi
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1261_ipc_dispatch.py" "$2" "$3" "$work/generated" --install;fi
if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1266_joined_ack.py" "$2" "$3" "$work/generated" --install;fi
if [[ "${4-}" == --irq-return ]];then python3 "$here/prepare_v1270_ipc_epilogue.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$reply_body_mode" == 1 ]];then python3 "$here/prepare_v1281_reply_fixture.py" "$2" "$3" "$work/generated" --install;fi
python3 "$here/patch_sc_trace_v570.py" "$work/generated"
python3 "$here/patch_sc_trace_v640.py" "$work/generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --vector "$work/input/vector.bin"
g++ -std=c++20 -O1 "${extra[@]}" -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_scheduler_postack_v1256.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { python3 "$here/classify_open_compile_v654.py" "$work/compile.log";echo 'V1256 compile failed';exit 1; }
rc=0;native_args=()
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then native_args=("$2");fi
ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$work/native" "${native_args[@]}" > "$work/run.log" 2>&1 || rc=$?
grep -Ex 'V1282_WAKE_ENTRY_TRIAL n=[0-7] original_processor=1 armmsg=1 native_dcbi=1 y1_w1c=1 queue=1 wake_executed=0|V1282_BODY_REFUSAL kind=[1-6] stage=[0-2] reason=[0-8] gate=[0-6] visits=[0-9]{1,4} reads=[0-9]{1,2} invalidations=[0-9]{1,3}|V1275_REPLY_DISPATCH_TRIAL n=[0-7] dispatcher=1 index=27 handler_entry=1 pending_reply=1|V1275_REPLY_ENTRY_TRIAL n=[0-7] original_handler=1 reply_processor_entry=1 pending_reply=1 waiting=1|V1275_REPLY_REFUSAL kind=[1-5] stage=[0-2] reason=[0-7] reads=[0-9]{1,2} visits=[0-9]{1,4}|V1271_RFI_TRIAL n=[0-7] original_scheduler=1 native_rfi=1 restored=1 reply_irq=1 waiting=1|V1271_REPLY_VECTOR_TRIAL n=[0-7] original_vector=1 trampoline=1 saved_fields=38 pending_reply=1 dispatcher_executed=0|V1271_EPILOGUE_REFUSAL kind=[1-8] stage=[0-5] reason=[0-9] entry=[0-9]{1,3} visits=[0-9]{1,3} select=[0-6]|V1266_ACK_TRIAL n=[0-7] handler_return=1 guest_w1c=1 native_reply=1 waiting=1 saved_fields=38|V1266_ACK_REFUSAL kind=[1-7] stage=[0-3] reason=[0-8] gate=[0-4] gate_reason=[0-3] visits=[0-9]{1,4}|V1261_DISPATCH_TRIAL n=[0-7] original_dispatcher=1 index=27 context=1 pi_reads=1 handler_entry=1 handler_executed=0|V1264_DOL_DATA verified=1 initialized_only=1 ranges=([1-9]|1[01])|V1261_DISPATCH_REFUSAL kind=[1-6] stage=[0-6] reason=[0-6] reads=[0-9]{1,2} detail=([0-9]|10) visits=[0-9]{1,4}|V1260_VECTOR_TRIAL n=[0-7] saved_fields=38 original_vector=1 trampoline=1 pending_ack=1 dispatcher_executed=0|V1260_VECTOR_REFUSAL kind=[1-4] stage=[0-3] reason=[0-6] gpr=[0-9]{1,10} special=[0-9]{1,2}|V1259_IRQ_TRIAL n=[0-7] entered=1 srr=1 registers=1 pending_ack=1 vector_executed=0|V1256_SCHED_POLL_REFUSAL stage=[1-6] category=[12]|V1254_SUBMIT_MMIO_REFUSAL category=[1-5] writes=[0-2] control=[01] low_bits=[0-9]{1,2} prior=[0-9]{1,2}|V1256_SCHED_TRIAL n=[0-7] saved=1 idle=1 enabled=1 pending_ack=1 irq_entered=0|V1252_SLEEP_TRIAL n=[0-7] waiting=1 queue=1 pending_ack=1 reply=0|V1256_OPEN_TRIAL n=[0-7] path=[12] request=1 native_rfi=1 serviced=0|V1256_SUBMIT_TRIAL n=[0-7] path=[12] ack=1 reply=0 si_quiescent=1|V1256_OPEN_FAILURE kind=(witness|assertion|interpreter|syscall|null_branch|mmio|mailbox|other) trial=[0-7] stage=[0-9]{1,2} reason=[0-7] line=[0-9]{1,4}' "$work/run.log" || true
[[ "$rc" == 0 ]] || { echo "V1256 execution failed rc=$rc";exit 1; }
grep -Fx 'V1256_SCHED_NATIVE owner=1 trials=8 submitted=8 ack=8 waiting=8 saved=8 idle=8 ee=8 pending_irq=8 irq_entered=0 reply=0 seeded_thread=1 synthetic_ack=1 synthetic_caller=1 synthetic_bridge=1 seeded_vector=1 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"

if [[ $# == 4 ]];then
  grep -Fx 'V1259_IRQ_NATIVE owner=1 trials=8 entered=8 saved=8 idle=8 pending_ack=8 vector_executed=0 reply=0 seeded_vector=1 fallback=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  grep -Fx 'V1260_VECTOR_NATIVE owner=1 trials=8 original_vector=8 trampoline=8 saved_fields=38 dispatcher_entry=8 dispatcher_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  grep -Fx 'V1261_DISPATCH_NATIVE owner=1 trials=8 dispatcher=8 ipc_index=27 handler_entry=8 handler_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  grep -Fx 'V1266_ACK_NATIVE owner=1 trials=8 original_dispatch=8 original_handler_return=8 native_reply=8 waiting=8 saved_fields=38 modeled_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-return ]];then
  grep -Fx 'V1271_REPLY_VECTOR_NATIVE owner=1 trials=8 first_rfi=8 restored=8 reply_irq=8 original_vector=8 trampoline=8 saved_fields=38 second_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$reply_entry_mode" == 1 ]];then
  grep -Fx 'V1275_REPLY_ENTRY_NATIVE owner=1 trials=8 original_second_dispatch=8 original_reply_handler=8 reply_processor_entry=8 waiting=8 ios_steps=2 wakeup=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$reply_body_mode" == 1 ]];then
  grep -Fx 'V1282_REPLY_WAKE_NATIVE owner=1 trials=8 original_processor=8 armmsg=8 native_dcbi=8 y1_w1c=8 original_wake_entry=8 waiting=8 ios_steps=2 wake_executed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi
