#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_transfer_callee_v916.py" "$dol" "$elf" "$work/owner_callback_prefix.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V881_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_transfer_callee_v916.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$here" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_transfer_callee_v916.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V881_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V881_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_transfer_callee_v916.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_transfer_callee_v916.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_packet_build_v887.py" "$work/build.log";python3 "$here/diagnose_build_v910.py" "$work/build.log" test_owner_transfer_callee_v916.cpp; echo "V881_NATIVE_BUILD failed=1";exit 1; }
  mkdir "$work/seeds"
  for trial in {0..7}; do
    timeout 20s "$work/probe" discover "$trial" "$work/seeds/$trial.txt" > "$work/run.log" 2>&1 || {
      grep -Ex 'V881_PREFIX_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-9]{1,2} visits=[0-9]{1,3} writes=[0-9]{1,2} choice=[0-4] memory=[0-5] packet_reads=[0-9]+ branches=[0-9]+ boundary=[0-9] time_stage=[0-5] time_failure=[0-7] post_failure=[0-4] post_memory=[0-5] post_visits=[0-9]{1,3}' "$work/run.log" || true
      grep -Ex 'V883_PACKET_(LOAD index=[1-4] region=[0-5] value_class=[0-3]|BRANCH index=[1-4] field_kind=[0-3] bit=[01])' "$work/run.log" || true
      echo 'V881_DISCOVERY failed=1';exit 1;
    }
    grep -Ex "V881_OWNER_PACKET_CHOICE trial=$trial free=0 next=3 visits=[0-9]{1,3} original_disable_return=1 call_executed=0 fallback=0 continuous_boot=0" "$work/run.log"
  done
  python3 "$here/validate_packet_seed_v881.py" "$work/seeds"
  for trial in {0..7}; do
    timeout 20s "$work/probe" open "$trial" "$work/seeds/$trial.txt" > "$work/run.log" 2>&1 || {
      grep -Ex 'V881_PREFIX_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-9]{1,2} visits=[0-9]{1,3} writes=[0-9]{1,2} choice=[0-4] memory=[0-5] packet_reads=[0-9]+ branches=[0-9]+ boundary=[0-9] time_stage=[0-5] time_failure=[0-7] post_failure=[0-4] post_memory=[0-5] post_visits=[0-9]{1,3}' "$work/run.log" || true
      grep -Ex 'V883_PACKET_(LOAD index=[1-4] region=[0-5] value_class=[0-3]|BRANCH index=[1-4] field_kind=[0-3] bit=[01])' "$work/run.log" || true
      grep -Ex 'V891_OWNER_TRANSFER_TIME original_return=1 leaves=3 abi=1 offset=1 nonzero=[01] wrap=[01] retry=[01] fallback=0 continuous_boot=0' "$work/run.log" || true
      echo 'V916_POST_TIME_LANE failed=1';exit 1;
    }
    grep -Ex "V891_OWNER_TRANSFER_TIME original_return=1 leaves=3 abi=1 offset=1 nonzero=[01] wrap=[01] retry=[01] fallback=0 continuous_boot=0" "$work/run.log"
    ordinal=6; if [[ "$trial" == 5 || "$trial" == 6 ]]; then ordinal=5; fi
    grep -Fx "V916_OWNER_NESTED_SAVE trial=$trial ordinal=$ordinal save_gprs=$ordinal writes=$((ordinal+2)) entry_abi=1 save_return=1 callee_return=0 fallback=0 continuous_boot=0" "$work/run.log"
    grep -Ex "V916_OWNER_CONTINUATION trial=$trial ordinal=$ordinal words=[1-9][0-9]? reads=[0-9]{1,2} writes=[0-8] save_return=1 next_disable=1 callee_return=0 fallback=0 continuous_boot=0" "$work/run.log"
    grep -Fx "V916_OWNER_DISABLE trial=$trial ordinal=$ordinal save_return=1 disable_return=1 leaf_visits=5 ee_preserved=1 callee_return=0 fallback=0 continuous_boot=0" "$work/run.log"
    if [[ "$ordinal" == 5 ]]; then
      grep -Fx "V916_OWNER_POST_DISABLE trial=$trial ordinal=5 words=4 reads=0 writes=2 time_call=1 fallback=0 continuous_boot=0" "$work/run.log"
      grep -Fx "V916_OWNER_ALARM_TIME trial=$trial original_return=1 leaves=3 abi=1 offset=1 fallback=0 continuous_boot=0" "$work/run.log"
    else
      grep -Fx "V916_OWNER_POST_DISABLE trial=$trial ordinal=6 words=3 reads=1 writes=0 time_call=0 fallback=0 continuous_boot=0" "$work/run.log"
    fi
  done
  for trial in 0 1 2 3 4 7; do
    timeout 20s "$work/probe" busy "$trial" "$work/seeds/$trial.txt" > "$work/run.log" 2>&1 || {
      grep -Ex 'V881_PREFIX_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-9]{1,2} visits=[0-9]{1,3} writes=[0-9]{1,2} choice=[0-4] memory=[0-5] packet_reads=[0-9]+ branches=[0-9]+ boundary=[0-9] time_stage=[0-5] time_failure=[0-7] post_failure=[0-4] post_memory=[0-5] post_visits=[0-9]{1,3}' "$work/run.log" || true
      grep -E '^V916_OWNER_POST_DISABLE trial=[0-7] ordinal=[56] words=[0-9]+ reads=[0-9]+ writes=[0-9]+ time_call=[01] fallback=0 continuous_boot=0$' "$work/run.log" || true
      echo 'V916_BUSY_RETURN failed=1';exit 1
    }
    grep -Fx "V916_OWNER_BUSY_RETURN trial=$trial original_return=1 irq_restore=1 gprs=6 abi=1 result=0 mmio=0 fallback=0 continuous_boot=0" "$work/run.log"
  done
  rc=0
  timeout 20s "$work/probe" busy_corrupt 0 "$work/seeds/0.txt" > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V916_BUSY_REFUSAL saved_word=1' "$work/run.log"
  for spec in result:1 offset:2; do
    rc=0
    timeout 20s "$work/probe" "${spec%:*}" 3 "$work/seeds/3.txt" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V891_TIME_REFUSAL kind=${spec#*:}" "$work/run.log"
  done
  rc=0
  timeout 20s "$work/probe" entry 3 "$work/seeds/3.txt" > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx "V916_CALLEE_REFUSAL link_corruption=1" "$work/run.log"
  for trial in 3 5; do
    rc=0
    timeout 20s "$work/probe" save "$trial" "$work/seeds/$trial.txt" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V916_NESTED_REFUSAL saved_word_corruption=1" "$work/run.log"
  done
  rm -rf -- "$work/seeds"
  rc=0
  timeout 20s "$work/probe" corrupt 0 "$work/unused.txt" > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V881_PREFIX_REFUSAL saved_word_corruption=1' "$work/run.log"
  echo "V881_PREFIX_MODE mode=$mode closed=8 time_returns=8 busy_returns=6 refused=7"
done
