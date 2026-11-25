#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_transfer_post_time_v893.py" "$dol" "$elf" "$work/owner_callback_prefix.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V881_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_transfer_post_time_v893.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$here" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_transfer_time_v891.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V881_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V881_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_transfer_post_time_v893.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -Wno-error=type-limits -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_transfer_post_time_v893.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_packet_build_v887.py" "$work/build.log";echo "V881_NATIVE_BUILD failed=1";exit 1; }
  mkdir "$work/seeds"
  for trial in {0..7}; do
    timeout 20s "$work/probe" discover "$trial" "$work/seeds/$trial.txt" > "$work/run.log" 2>&1 || {
      grep -Ex 'V881_PREFIX_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-8] visits=[0-9]{1,3} writes=[0-9]{1,2} choice=[0-4] memory=[0-5] packet_reads=[0-9]+ branches=[0-9]+ boundary=[0-9] time_stage=[0-5] time_failure=[0-7] post_failure=[0-4] post_memory=[0-5] post_visits=[0-9]{1,3}' "$work/run.log" || true
      grep -Ex 'V883_PACKET_(LOAD index=[1-4] region=[0-5] value_class=[0-3]|BRANCH index=[1-4] field_kind=[0-3] bit=[01])' "$work/run.log" || true
      echo 'V881_DISCOVERY failed=1';exit 1;
    }
    grep -Ex "V881_OWNER_PACKET_CHOICE trial=$trial free=0 next=3 visits=[0-9]{1,3} original_disable_return=1 call_executed=0 fallback=0 continuous_boot=0" "$work/run.log"
  done
  python3 "$here/validate_packet_seed_v881.py" "$work/seeds"
  for trial in {0..7}; do
    timeout 20s "$work/probe" open "$trial" "$work/seeds/$trial.txt" > "$work/run.log" 2>&1 || {
      grep -Ex 'V881_PREFIX_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-8] visits=[0-9]{1,3} writes=[0-9]{1,2} choice=[0-4] memory=[0-5] packet_reads=[0-9]+ branches=[0-9]+ boundary=[0-9] time_stage=[0-5] time_failure=[0-7] post_failure=[0-4] post_memory=[0-5] post_visits=[0-9]{1,3}' "$work/run.log" || true
      grep -Ex 'V883_PACKET_(LOAD index=[1-4] region=[0-5] value_class=[0-3]|BRANCH index=[1-4] field_kind=[0-3] bit=[01])' "$work/run.log" || true
      grep -Ex 'V891_OWNER_TRANSFER_TIME original_return=1 leaves=3 abi=1 offset=1 nonzero=[01] wrap=[01] retry=[01] fallback=0 continuous_boot=0' "$work/run.log" || true
      echo 'V893_POST_TIME_LANE failed=1';exit 1;
    }
    grep -Ex "V891_OWNER_TRANSFER_TIME original_return=1 leaves=3 abi=1 offset=1 nonzero=[01] wrap=[01] retry=[01] fallback=0 continuous_boot=0" "$work/run.log"
    grep -Ex "V893_OWNER_POST_TIME trial=$trial next=[5-9] visits=[0-9]{1,3} writes=[0-8] original_time_return=1 next_call_executed=0 fallback=0 continuous_boot=0" "$work/run.log"
  done
  for spec in result:1 offset:2; do
    rc=0
    timeout 20s "$work/probe" "${spec%:*}" 3 "$work/seeds/3.txt" > "$work/run.log" 2>&1 || rc=$?
    [[ "$rc" == 126 ]]
    grep -Fx "V891_TIME_REFUSAL kind=${spec#*:}" "$work/run.log"
  done
  rm -rf -- "$work/seeds"
  rc=0
  timeout 20s "$work/probe" corrupt 0 "$work/unused.txt" > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V881_PREFIX_REFUSAL saved_word_corruption=1' "$work/run.log"
  echo "V881_PREFIX_MODE mode=$mode closed=8 time_returns=8 refused=3"
done
