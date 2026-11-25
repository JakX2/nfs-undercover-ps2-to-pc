#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_exi_write_v828.py" "$dol" "$elf" "$work/owner_exi_write.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V828_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_exi_write_v828.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_exi_write_v828.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V828_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V828_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_exi_write_v828.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_exi_write_v828.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V828_NATIVE_BUILD failed=1";exit 1; }
  for trial in {0..3}; do
    timeout 30s "$work/probe" valid "$trial" > "$work/run.log" 2>&1 || {
      grep -Ex 'V828_EXI_FAULT kind=[1-8] line=[0-9]{1,4} depth=[0-9]{1,2} visits=[0-9]{1,5} entries=[0-9]{1,4} imm=[0-9]{1,2} imm_return=[0-9]{1,2} sync=[0-9]{1,2} sync_return=[0-9]{1,2} completed=[0-9]{1,2} reads=[0-9]{1,4} writes=[0-9]{1,3} polls=[0-9]{1,4} witness=[0-6]' "$work/run.log" || true
      echo 'V828_NATIVE_EXECUTION failed=1';exit 1;
    }
    grep -Fx 'V828_OWNER_EXI_WRITE original_imm=12 original_sync=12 transfers=12 bytes=44 payload=1 abi=1 fallback=0 continuous_boot=0' "$work/run.log"
  done
  for fault in delayed bad-payload; do
    rc=0
    timeout 30s "$work/probe" "$fault" 0 > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    if [[ "$fault" == delayed ]]; then
      grep -Fx 'V828_EXI_REFUSAL timeout=1 original_sync_pending=1 completed=0' "$work/run.log"
    else
      grep -Fx 'V828_EXI_REFUSAL payload=1 completed=2' "$work/run.log"
    fi
  done
  echo "V828_EXI_MODE mode=$mode valid=4 refused=2"
done
