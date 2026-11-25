#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
full=();flags=();if [[ "${UNDERCOVER_TEST_CALLBACK_RETURN:-0}" == 1 ]];then full+=(--callback-return);flags+=(-DUNDERCOVER_TEST_CALLBACK_RETURN=1);fi
python3 "$here/prepare_owner_callback_after_setter_v842.py" "$dol" "$elf" "$work/owner_callback_write.h" "${full[@]}"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V820_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_callback_after_setter_v842.py" "$dol" "$elf" "$root" --patch-analyzer "${full[@]}"
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_callback_write_v838.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V820_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V820_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_callback_after_setter_v842.py" "$dol" "$elf" "$work/$mode" --install "${full[@]}"
  g++ "${flags[@]}" -DUNDERCOVER_TEST_AFTER_SETTER=1 -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_callback_write_v838.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || {
    python3 - "$work/build.log" <<'PY'
import re,sys
from pathlib import Path
raw=Path(sys.argv[1]).read_text(errors='replace')
for l in raw.splitlines():
    m=re.search(r'(test_owner_callback_write_v838\.cpp|callback_write_fixture_v838\.h):(\d{1,4}):\d+:\s*(?:fatal )?(error|warning):',l)
    if m: print('V840_BUILD_DIAG source='+('harness' if m[1].endswith('.cpp') else 'observer')+' line='+m[2]+' class='+m[3])
print('V840_BUILD_DIAG errors='+str(min(999,len(re.findall(r'\berror:',raw)))))
PY
    echo "V838_NATIVE_BUILD failed=1";exit 1;
  }
  nonzero=0;wrap=0;retry=0;first_upper_delta=0
  for trial in {0..7}; do
    timeout 20s "$work/probe" valid "$trial" > "$work/run.log" 2>&1 || {
      grep -Ex 'V802_CALLBACK_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-7] visits=[0-9]{1,3} writes=[0-9]{1,2}' "$work/run.log" || true
      grep -Ex 'V810_TIME_WITNESS stage=[0-5] reason=[0-7] visits=[0-9]{1,3} cursor=[0-3]' "$work/run.log" || true
      grep -Ex 'V820_FRONTIER_DIAG active=[01] visits=[0-9]{1,2} writes=[0-3]|V816_WIRELESS_FAULT kind=[1-8] line=[0-9]{1,4} lane=[0-2] depth=[0-9]{1,2} visits=[0-9]{1,5} entries=[0-9]{1,4} unlocks=[0-9] disables=[0-9]{1,3} restores=[0-9]{1,3}|V837_RETURN_DIAG exi_unlock=[0-9] exi_return=[0-9] sram_return=[0-9]|V842_SUFFIX_DIAG stage=[0-2] reason=[0-7] visits=[0-9]{1,3} polls=[0-9]{1,3}|V846_RETURN_DIAG stage=[0-5] reason=[0-5] visits=[0-9]{1,2}' "$work/run.log" || true
      echo "V838_NATIVE_EXECUTION failed=1";exit 1;
    }
    grep -Fx 'V810_OWNER_TIME_WITNESS verified=1 leaves=3 abi=1 timebase=1 callback_return=0' "$work/run.log"
    grep -Fx 'V829_OWNER_FRONTIER verified=1 store_bytes=1 ordinal=3' "$work/run.log"
    grep -Fx 'V826_OWNER_CALLBACK_WIRELESS original_time_return=1 original_setter_return=1 abi=1 unchanged=1 exi=0 callback_return=0 fallback=0 continuous_boot=0' "$work/run.log"
    grep -Ex 'V842_OWNER_CALLBACK_SUFFIX ordinal=(4|13) target_class=[0-4] visits=[0-9]{1,3} writes=[0-8] polls=[0-9]{1,3} setter_return=1 changed=0 target_executed=0 callback_return=0 fallback=0 continuous_boot=0' "$work/run.log"
    if [[ ${#full[@]} != 0 ]];then grep -Fx 'V846_OWNER_CALLBACK_RETURN original_restore=1 callback_return=1 abi=1 visits=12 changed=0 fallback=0 continuous_boot=0' "$work/run.log";fi
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
  grep -Ex 'V823_TIME_COUNTS leaf_visits=[0-9]{1,3} polls=[0-9]{1,2} reads=[0-9]{1,3}' "$work/run.log"
  echo "V814_TIMEBASE_MODE mode=$mode targeted_retry=1"
  echo "V811_OFFSET_MODE mode=$mode valid=8 nonzero=$nonzero wrap=$wrap retry=$retry refused=3"
  rc=0
  timeout 20s "$work/probe" frontier-corrupt 0 > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx "V820_FRONTIER_REFUSAL identity=1" "$work/run.log"
  for trial in {0..7}; do
    timeout 20s "$work/probe" wireless-changed "$trial" > "$work/run.log" 2>&1 || {
      grep -Ex 'V802_CALLBACK_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-9] visits=[0-9]{1,3} writes=[0-9]{1,2}|V816_WIRELESS_FAULT kind=[1-8] line=[0-9]{1,4} lane=[0-2] depth=[0-9]{1,2} visits=[0-9]{1,5} entries=[0-9]{1,4} unlocks=[0-9] disables=[0-9]{1,3} restores=[0-9]{1,3}|V837_RETURN_DIAG exi_unlock=[0-9] exi_return=[0-9] sram_return=[0-9]|V842_SUFFIX_DIAG stage=[0-2] reason=[0-7] visits=[0-9]{1,3} polls=[0-9]{1,3}|V846_RETURN_DIAG stage=[0-5] reason=[0-5] visits=[0-9]{1,2}' "$work/run.log" || true
      echo 'V826_CHANGED_EXECUTION failed=1';exit 1;
    }
    grep -Fx 'V829_OWNER_FRONTIER verified=1 store_bytes=1 ordinal=3' "$work/run.log"
    grep -Fx 'V838_OWNER_CALLBACK_WRITE original_time_return=1 original_setter_return=1 original_unlock=1 bytes=44 payload=1 abi=1 callback_return=0 fallback=0 continuous_boot=0' "$work/run.log"
    grep -Ex 'V842_OWNER_CALLBACK_SUFFIX ordinal=(4|13) target_class=[0-4] visits=[0-9]{1,3} writes=[0-8] polls=[0-9]{1,3} setter_return=1 changed=1 target_executed=0 callback_return=0 fallback=0 continuous_boot=0' "$work/run.log"
    if [[ ${#full[@]} != 0 ]];then grep -Fx 'V846_OWNER_CALLBACK_RETURN original_restore=1 callback_return=1 abi=1 visits=12 changed=1 fallback=0 continuous_boot=0' "$work/run.log";fi
  done
  rc=0
  timeout 20s "$work/probe" wireless-corrupt 0 > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V826_JOIN_REFUSAL abi=1' "$work/run.log"
  rc=0
  timeout 20s "$work/probe" changed-corrupt 0 > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V826_JOIN_REFUSAL abi=1' "$work/run.log"
  if [[ ${#full[@]} != 0 ]];then
    rc=0
    timeout 20s "$work/probe" return-corrupt 0 > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx 'V846_RETURN_REFUSAL abi=1' "$work/run.log"
    echo "V846_RETURN_MODE mode=$mode valid=16 refused=1"
  fi
  echo "V842_SUFFIX_MODE mode=$mode unchanged=8 changed_return=8 refused=2"
  echo "V802_CALLBACK_MODE mode=$mode valid=8 refused=1"
done
