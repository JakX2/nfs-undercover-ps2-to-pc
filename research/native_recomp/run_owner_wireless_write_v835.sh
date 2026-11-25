#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_wireless_write_v835.py" "$dol" "$elf" "$work/owner_wireless_write.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V835_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_wireless_write_v835.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_wireless_write_v835.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V835_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V835_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_wireless_write_v835.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_wireless_write_v835.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V835_NATIVE_BUILD failed=1";exit 1; }
  for mode_case in get same changed; do
    for trial in {0..3}; do
      timeout 20s "$work/probe" "$mode_case" "$trial" > "$work/run.log" 2>&1 || {
        grep -Ex 'V816_WIRELESS_FAULT kind=[1-8] line=[0-9]{1,4} lane=[0-2] depth=[0-9]{1,2} visits=[0-9]{1,4} entries=[0-9]{1,3} unlocks=[0-9] disables=[0-9]{1,2} restores=[0-9]{1,2}' "$work/run.log" || true
        grep -Ex 'V819_LOCK_DIAG lock=[0-9] returned=[0-9] masks=[0-9] reads=[0-9]{1,2} writes=[0-9]{1,2} polls=[0-9]{1,3}|V825_SELECT_DIAG selected=[0-9] returned=[0-9]' "$work/run.log" || true
        grep -Ex 'V835_WRITE_DIAG imm=[0-9]{1,2} imm_return=[0-9]{1,2} sync=[0-9]{1,2} sync_return=[0-9]{1,2} extended=[0-9] deselect=[0-9] completed=[0-9]{1,2} witness=[0-6]' "$work/run.log" || true
        echo 'V835_NATIVE_EXECUTION failed=1';exit 1;
      }
      if [[ "$mode_case" == changed ]]; then
        grep -Fx 'V835_OWNER_WIRELESS_WRITE original_lock=1 original_select=1 original_imm=12 original_sync=12 original_immex=1 original_deselect=1 bytes=44 payload=1 unlock_entry=1 wrapper_return=0 fallback=0 continuous_boot=0' "$work/run.log"
      else
        lane=0;[[ "$mode_case" != same ]] || lane=1
        grep -Fx "V816_OWNER_WIRELESS_RETURN lane=$lane original_wrapper=1 unlock=1 abi=1 payload=1 exi=0 fallback=0 continuous_boot=0" "$work/run.log"
      fi
    done
  done
  rc=0
  timeout 20s "$work/probe" corrupt 0 > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V816_WIRELESS_REFUSAL abi=1' "$work/run.log"
  echo "V835_WIRELESS_MODE mode=$mode get=4 unchanged=4 write_return=4 refused=1"
done
