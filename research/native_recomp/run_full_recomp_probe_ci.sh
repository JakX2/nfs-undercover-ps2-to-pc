#!/usr/bin/env bash
# Private whole-image translation, syntax, native link and optional bounded startup.
# Startup, hardware, cache, data, os-entry, os-time, os-hardware, os-arena, os-ipc, os-vector, os-pack, os-alarm, os-irq, os-mmio, os-irq-return, os-context, os-cache-reuse, os-exi-poll, os-exi-handlers, os-exi-id, os-exi-absent, os-si-entry, os-si-sample, os-si-return and os-sram modes launch bounded witnesses; never claim game boot.
set -euo pipefail
if [[ $# -ne 5 ]]; then
  echo 'Usage: run_full_recomp_probe_ci.sh NWII_ROOT OWNER_DOL OWNER_ELF PRIVATE_WORK sample|all|link|startup|hardware|cache|data|os-entry|os-time|os-hardware|os-arena|os-ipc|os-vector|os-pack|os-alarm|os-irq|os-mmio|os-irq-return|os-context|os-cache-reuse|os-exi-poll|os-exi-handlers|os-exi-id|os-exi-absent|os-si-entry|os-si-sample|os-si-return|os-sram' >&2
  exit 2
fi
root="$(realpath "$1")"
dol="$(realpath "$2")"
elf="$(realpath "$3")"
work="$4"
mode="$5"
[[ "$mode" == sample || "$mode" == all || "$mode" == link || "$mode" == startup || "$mode" == hardware || "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]] || { echo 'Invalid compile probe mode' >&2; exit 2; }
[[ ! -e "$work" ]] || { echo 'Private work destination must be fresh' >&2; exit 2; }
mkdir -p -m 700 "$work"
here="$(cd "$(dirname "$0")" && pwd)"
umask 077
python3 "$here/make_private_elf_symbol_map.py" "$elf" "$work/functions-private.csv"
python3 "$here/apply_psq_indexed_patch.py" "$root" > "$work/patch.log" 2>&1 || {
  echo 'Indexed paired-single patch failed' >&2; exit 1;
}
python3 "$here/apply_psq_estimate_and_gqr_v5.py" "$root" >> "$work/patch.log" 2>&1 || {
  echo 'Paired-single runtime patch failed' >&2; exit 1;
}
python3 "$here/apply_verified_elf_spans_v6.py" "$root" >> "$work/patch.log" 2>&1 || {
  echo 'Conservative ELF code-span patch failed' >&2; exit 1;
}
if [[ "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  python3 "$here/apply_function_root_v443.py" "$root" >> "$work/patch.log" 2>&1 || {
    echo 'V443 function root patch failed' >&2; exit 1;
  }
  if [[ "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
    for patch in apply_exact_dispatch_v445 apply_native_tick_v438; do
      python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
        echo 'V446 validated dispatcher/tick patch failed' >&2; exit 1;
      }
    done
  fi
  python3 "$here/apply_perf_sprs_v29.py" "$root" >> "$work/patch.log" 2>&1 || {
    echo 'V439 performance runtime patch failed' >&2; exit 1;
  }
fi
if [[ "$mode" == hardware || "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  # Reuse earlier independently validated register implementations only
  # in the extended lane. V419 remains the unmodified control.
  for patch in apply_hid_state_v18 apply_fpscr_v19; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V425 hardware runtime patch failed' >&2; exit 1;
    }
  done
fi
if [[ "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  # Bounded guest L2CR handshake and explicit mtmsr resume PCs, previously
  # validated in isolated execution. Do not replace any original OS body.
  for patch in apply_l2cr_v20 apply_mtmsr_resume_v74; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V428 cache runtime patch failed' >&2; exit 1;
    }
  done
fi
if [[ "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  for patch in verify_perf_combo_v29 apply_hid4_continuous_v30; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V439 combined hardware runtime patch failed' >&2; exit 1;
    }
  done
fi
if [[ "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  # V456 independently verified this exact cache patch composition.
  for patch in apply_cache_continuous_v39 apply_cache_trace_v44 apply_dcbz_v67 apply_cache_order_v456; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V460 native cache runtime patch failed' >&2; exit 1;
    }
  done
fi
if [[ "$mode" == os-sram ]]; then
  python3 "$here/apply_data_cache_invalidate_v532.py" "$root" >> "$work/patch.log" 2>&1 || { echo "V532 native dcbi patch failed" >&2; exit 1; }
fi
if [[ "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  python3 "$here/apply_exi_tick_v497.py" "$root" emitter >> "$work/patch.log" 2>&1 || { echo "V497 EXI emitter patch failed" >&2; exit 1; }
fi
if [[ "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  python3 "$here/apply_si_tick_v515.py" "$root" emitter >> "$work/patch.log" 2>&1 || { echo "V515 SI emitter patch failed" >&2; exit 1; }
fi
mkdir -p "$work/generated" "$work/bin"
g++ -std=c++20 -O2 -Wno-unused-variable -Wno-sign-compare \
  -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" -o "$work/bin/translator" \
  > "$work/build.log" 2>&1 || {
    echo 'Whole-image offline translator failed to compile' >&2; exit 1;
  }
timeout 1200s "$work/bin/translator" "$dol" "$work/functions-private.csv" \
  "$work/generated" --strict-symbol-spans --generate "$root/nWiiRuntime" \
  > "$work/translation.log" 2>&1 || {
    echo 'Original whole-image translation failed; private diagnostics withheld' >&2; exit 1;
  }
count="$(find "$work/generated" -maxdepth 1 -type f -name 'output_*.cpp' | wc -l)"
(( count >= 20 )) || { echo 'Generated too few private C++ shards' >&2; exit 1; }
[[ -s "$work/generated/main_output.cpp" ]] || {
  echo 'Generated C++ dispatcher missing' >&2; exit 1;
}
if grep -lF 'UNIMPLEMENTED Opcode' "$work/generated"/output_*.cpp > "$work/opcode-failures.log"; then
  echo 'Explicit unsupported opcode markers remain in full-image translation' >&2
  exit 1
fi
# Authenticate the observer before the expensive all-shard syntax pass.
if [[ "$mode" == os-hardware ]]; then
  python3 "$here/prepare_v439_full_os_hardware.py" "$dol" "$work/generated"
elif [[ "$mode" == os-arena ]]; then
  python3 "$here/prepare_v444_full_os_arena.py" "$dol" "$work/generated"
elif [[ "$mode" == os-ipc ]]; then
  python3 "$here/prepare_v446_full_os_ipc.py" "$dol" "$work/generated"
elif [[ "$mode" == os-vector ]]; then
  python3 "$here/prepare_v457_exception_vector.py" "$dol" "$work/generated"
elif [[ "$mode" == os-pack ]]; then
  python3 "$here/prepare_v466_exception_pack.py" "$dol" "$work/generated"
elif [[ "$mode" == os-alarm ]]; then
  python3 "$here/prepare_v470_alarm_startup.py" "$dol" "$work/generated"
elif [[ "$mode" == os-irq ]]; then
  python3 "$here/prepare_v473_module_irq.py" "$dol" "$work/generated"
elif [[ "$mode" == os-mmio ]]; then
  python3 "$here/prepare_v476_irq_mmio.py" "$dol" "$work/generated"
elif [[ "$mode" == os-irq-return ]]; then
  python3 "$here/prepare_v483_irq_return.py" "$dol" "$work/generated"
elif [[ "$mode" == os-context ]]; then
  python3 "$here/prepare_v486_context_startup.py" "$dol" "$work/generated"
elif [[ "$mode" == os-cache-reuse ]]; then
  python3 "$here/prepare_v488_os_cache_reuse.py" "$dol" "$work/generated"
elif [[ "$mode" == os-exi-poll ]]; then
  python3 "$here/prepare_v491_exi_poll.py" "$dol" "$work/generated"
elif [[ "$mode" == os-exi-handlers ]]; then
  python3 "$here/prepare_v500_exi_handlers.py" "$dol" "$work/generated"
elif [[ "$mode" == os-exi-id ]]; then
  python3 "$here/prepare_v504_exi_id.py" "$dol" "$work/generated"
elif [[ "$mode" == os-exi-absent ]]; then
  python3 "$here/prepare_v510_exi_absent.py" "$dol" "$work/generated"
elif [[ "$mode" == os-si-entry ]]; then
  python3 "$here/prepare_v520_si_entry.py" "$dol" "$work/generated"
elif [[ "$mode" == os-sram ]]; then
  python3 "$here/prepare_v534_sram_read.py" "$dol" "$work/generated"
elif [[ "$mode" == os-si-return ]]; then
  python3 "$here/prepare_v529_si_discovery.py" "$dol" "$work/generated"
elif [[ "$mode" == os-si-sample ]]; then
  python3 "$here/prepare_v524_si_sampling.py" "$dol" "$work/generated"
fi
if [[ "$mode" == sample ]]; then
  first="$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | sort | head -1)"
  last="$(find "$work/generated" -maxdepth 1 -name 'output_*.cpp' | sort | tail -1)"
  set -- "$first" "$last" "$work/generated/main_output.cpp"
else
  set -- "$work/generated"/output_*.cpp "$work/generated/main_output.cpp"
fi
checks="$#"
for cpp in "$@"; do
  timeout 90s g++ -std=c++20 -fsyntax-only -fmax-errors=3 \
    -I"$work/generated/nWiiRuntime/include" -I"$work/generated" "$cpp" \
    > "$work/syntax.log" 2>&1 || {
      echo 'Private translated C++ syntax check failed; source withheld' >&2; exit 1;
    }
done
echo "PASS: whole Wii DOL translated into $count ephemeral C++ shards"
echo "PASS: translated syntax checks $checks/$checks mode=$mode"
if [[ "$mode" == startup ]]; then
  python3 "$here/prepare_v419_full_start.py" "$dol" "$work/generated"
elif [[ "$mode" == hardware ]]; then
  python3 "$here/prepare_v425_full_hardware.py" "$dol" "$work/generated"
elif [[ "$mode" == cache ]]; then
  python3 "$here/prepare_v428_full_cache.py" "$dol" "$work/generated"
elif [[ "$mode" == data ]]; then
  python3 "$here/prepare_v430_full_data.py" "$dol" "$work/generated"
elif [[ "$mode" == os-entry ]]; then
  python3 "$here/prepare_v433_full_os_entry.py" "$dol" "$work/generated"
elif [[ "$mode" == os-time ]]; then
  python3 "$here/prepare_v435_full_os_time.py" "$dol" "$work/generated"
fi
if [[ "$mode" == link || "$mode" == startup || "$mode" == hardware || "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc || "$mode" == os-vector || "$mode" == os-pack || "$mode" == os-alarm || "$mode" == os-irq || "$mode" == os-mmio || "$mode" == os-irq-return || "$mode" == os-context || "$mode" == os-cache-reuse || "$mode" == os-exi-poll || "$mode" == os-exi-handlers || "$mode" == os-exi-id || "$mode" == os-exi-absent || "$mode" == os-si-entry || "$mode" == os-si-sample || "$mode" == os-si-return || "$mode" == os-sram ]]; then
  bash "$here/run_private_full_link.sh" "$work/generated" "$work/native-build"
  if [[ "$mode" == startup ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run"
    echo 'INFO: bounded native entry and register initialization only; hardware body, main, boot, frontend and gameplay NOT proven'
  elif [[ "$mode" == hardware ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" hardware
    echo 'INFO: bounded native PS/FPR initialization only; cache body, main, boot, frontend and gameplay NOT proven'
  elif [[ "$mode" == cache ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" cache
    echo 'INFO: bounded native cache control and error-handler registration only; data body, OSInit, main, boot and gameplay NOT proven'
  elif [[ "$mode" == data ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" data
    echo 'INFO: bounded native data initialization and original return only; DBInit, OSInit, main, boot and gameplay NOT proven'
  elif [[ "$mode" == os-entry ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-entry
    echo 'INFO: bounded DBInit return and OSInit entry only; OSInit body, main, boot and gameplay NOT proven'
  elif [[ "$mode" == os-time ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-time
    echo 'INFO: bounded original OSInit prologue and system-time return only; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-hardware ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-hardware
    echo 'INFO: bounded original OSInit hardware-value setup only; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-arena ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-arena
    echo 'INFO: bounded original OSInit MEM1 arena stores; MEM2, OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-ipc ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-ipc
    echo 'INFO: bounded original MEM2 and IPC pointer stores, OSExceptionInit entry only; IOS communication, OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-vector ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-vector
    echo 'INFO: bounded first original exception-vector copy and cache ordering only; exception dispatch, OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-pack ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-pack
    echo 'INFO: bounded original exception pack and system-call overlay; alarm entry only, OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-alarm ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-alarm
    echo 'INFO: bounded original alarm/shutdown registration and module entry; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-irq ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-irq
    echo 'INFO: bounded original module and IRQ table memset return; IRQ MMIO, OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-mmio ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-mmio
    echo 'INFO: bounded original IRQ PI/Hollywood mask writes and disable entry; IRQ completion, OSInit return, main and gameplay NOT proven'
  elif [[ "$mode" == os-irq-return ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-irq-return
    echo 'INFO: bounded original IRQ seven-bank mask loop and return to context initializer entry; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-context ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-context
    echo 'INFO: bounded original context initialization and cache entry; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-cache-reuse ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-cache-reuse
    echo 'INFO: bounded original second cache initialization and EXI entry; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-exi-poll ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-exi-poll
    echo 'INFO: bounded original EXI cold polling and interrupt mask entry; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-exi-handlers ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-exi-handlers
    echo 'INFO: bounded original EXI interrupt mask and handler registration; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-exi-id ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-exi-id
    echo 'INFO: bounded original EXI ID with explicit synthetic device profile; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-exi-absent ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-exi-absent
    echo 'INFO: bounded original removable-card discovery and version entry; OSInit completion, main and gameplay NOT proven'
  elif [[ "$mode" == os-sram ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-sram
    echo 'INFO: bounded original SRAM read DMA and OSInit continuation; thread init, main and gameplay NOT proven'
  elif [[ "$mode" == os-si-return ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-si-return
    echo 'INFO: bounded original SI return and SRAM initializer entry; SRAM return, main and gameplay NOT proven'
  elif [[ "$mode" == os-si-sample ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-si-sample
    echo 'INFO: bounded original SI sampling and interrupt registration; SI return, main and gameplay NOT proven'
  elif [[ "$mode" == os-si-entry ]]; then
    bash "$here/run_private_full_start.sh" "$work/native-build/bin/UndercoverWiiLocal" "$dol" "$work/startup-run" os-si-entry
    echo 'INFO: bounded original EXI return and SI cold setup entry; OSInit completion, main and gameplay NOT proven'
  else
    echo 'INFO: native game launch, main, boot, frontend and gameplay NOT proven'
  fi
else
  echo 'INFO: original full-image linking, game main, boot, frontend and gameplay NOT proven'
fi
