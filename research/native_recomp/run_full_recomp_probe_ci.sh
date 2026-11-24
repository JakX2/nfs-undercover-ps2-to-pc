#!/usr/bin/env bash
# Private whole-image translation, syntax, native link and optional bounded startup.
# Startup, hardware, cache, data, os-entry, os-time, os-hardware, os-arena and os-ipc modes launch bounded witnesses; never claim game boot.
set -euo pipefail
if [[ $# -ne 5 ]]; then
  echo 'Usage: run_full_recomp_probe_ci.sh NWII_ROOT OWNER_DOL OWNER_ELF PRIVATE_WORK sample|all|link|startup|hardware|cache|data|os-entry|os-time|os-hardware|os-arena|os-ipc' >&2
  exit 2
fi
root="$(realpath "$1")"
dol="$(realpath "$2")"
elf="$(realpath "$3")"
work="$4"
mode="$5"
[[ "$mode" == sample || "$mode" == all || "$mode" == link || "$mode" == startup || "$mode" == hardware || "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc ]] || { echo 'Invalid compile probe mode' >&2; exit 2; }
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
if [[ "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc ]]; then
  python3 "$here/apply_function_root_v443.py" "$root" >> "$work/patch.log" 2>&1 || {
    echo 'V443 function root patch failed' >&2; exit 1;
  }
  if [[ "$mode" == os-ipc ]]; then
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
if [[ "$mode" == hardware || "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc ]]; then
  # Reuse earlier independently validated register implementations only
  # in the extended lane. V419 remains the unmodified control.
  for patch in apply_hid_state_v18 apply_fpscr_v19; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V425 hardware runtime patch failed' >&2; exit 1;
    }
  done
fi
if [[ "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc ]]; then
  # Bounded guest L2CR handshake and explicit mtmsr resume PCs, previously
  # validated in isolated execution. Do not replace any original OS body.
  for patch in apply_l2cr_v20 apply_mtmsr_resume_v74; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V428 cache runtime patch failed' >&2; exit 1;
    }
  done
fi
if [[ "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc ]]; then
  for patch in verify_perf_combo_v29 apply_hid4_continuous_v30; do
    python3 "$here/$patch.py" "$root" >> "$work/patch.log" 2>&1 || {
      echo 'V439 combined hardware runtime patch failed' >&2; exit 1;
    }
  done
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
if [[ "$mode" == link || "$mode" == startup || "$mode" == hardware || "$mode" == cache || "$mode" == data || "$mode" == os-entry || "$mode" == os-time || "$mode" == os-hardware || "$mode" == os-arena || "$mode" == os-ipc ]]; then
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
  else
    echo 'INFO: native game launch, main, boot, frontend and gameplay NOT proven'
  fi
else
  echo 'INFO: original full-image linking, game main, boot, frontend and gameplay NOT proven'
fi
