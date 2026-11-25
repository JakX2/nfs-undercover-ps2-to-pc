#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_callback_time_v802.py" "$dol" "$elf" "$work/owner_callback_time.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V802_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_callback_time_v802.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_callback_time_v802.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V802_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V802_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_callback_time_v802.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_callback_time_v802.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V802_NATIVE_BUILD failed=1";exit 1; }
  nonzero=0;wrap=0;retry=0;first_upper_delta=0
  for trial in {0..7}; do
    timeout 20s "$work/probe" valid "$trial" > "$work/run.log" 2>&1 || {
      grep -Ex 'V802_CALLBACK_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-7] visits=[0-9]{1,3} writes=[0-9]{1,2}' "$work/run.log" || true
      grep -Ex 'V810_TIME_WITNESS stage=[0-5] reason=[0-7] visits=[0-9]{1,3} cursor=[0-3]' "$work/run.log" || true
      echo "V802_NATIVE_EXECUTION failed=1";exit 1;
    }
    grep -Fx 'V810_OWNER_TIME_WITNESS verified=1 leaves=3 abi=1 timebase=1 callback_return=0' "$work/run.log"
    row=$(grep -Ex 'V811_OWNER_TIME_OFFSET verified=1 nonzero=[01] wrap=[01] retry=[01]' "$work/run.log")
    echo "$row"
    if [[ "$trial" == 0 ]]; then
      geometry=$(grep -Ex 'V814_TIMEBASE_GEOMETRY first_upper_delta=[0-9]{1,3}' "$work/run.log")
      first_upper_delta=${geometry##*=}
      [[ "$first_upper_delta" -ge 1 && "$first_upper_delta" -le 160 ]]
    fi
    [[ "$row" != *'nonzero=1'* ]] || nonzero=$((nonzero+1))
    [[ "$row" != *'wrap=1'* ]] || wrap=$((wrap+1))
    [[ "$row" != *'retry=1'* ]] || retry=$((retry+1))
    grep -Fx 'V802_OWNER_CALLBACK_TIME original_prologue=1 original_time_return=1 leaves=3 timebase=1 callback_return=0 fallback=0 continuous_boot=0' "$work/run.log"
  done
  rc=0
  timeout 20s "$work/probe" corrupt 0 > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V802_CALLBACK_REFUSAL abi=1' "$work/run.log"
  for spec in result:2 offset:3; do
    rc=0
    timeout 20s "$work/probe" "${spec%:*}" 3 > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V811_OFFSET_REFUSAL kind=${spec#*:}" "$work/run.log"
  done
  [[ "$nonzero" == 7 && "$wrap" -ge 1 ]]
  # Place the FIRST real TBU sample at 0xffffffff, guaranteeing a
  # high-word change before the next TBU read in the original leaf.
  start=$((4294967295-first_upper_delta))
  timeout 20s "$work/probe" rollover 0 "$start" > "$work/run.log" 2>&1 || {
    grep -Ex 'V802_CALLBACK_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-7] visits=[0-9]{1,3} writes=[0-9]{1,2}|V810_TIME_WITNESS stage=[0-5] reason=[0-7] visits=[0-9]{1,3} cursor=[0-3]' "$work/run.log" || true
    echo 'V814_RETRY_EXECUTION failed=1';exit 1;
  }
  grep -Fx 'V814_TIMEBASE_RETRY verified=1 original_retry=1 original_time_return=1 offset=1 fallback=0' "$work/run.log"
  echo "V814_TIMEBASE_MODE mode=$mode targeted_retry=1"
  echo "V811_OFFSET_MODE mode=$mode valid=8 nonzero=$nonzero wrap=$wrap retry=$retry refused=3"
  echo "V802_CALLBACK_MODE mode=$mode valid=8 refused=1"
done
