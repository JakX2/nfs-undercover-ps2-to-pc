#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_epilogue_v737.py" "$dol" "$elf" "$work/owner_epilogue_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V737_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_epilogue_v737.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_epilogue_v737.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V737_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V737_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_epilogue_v737.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_live_epilogue_v762.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { echo "V737_NATIVE_BUILD failed=1";exit 1; }
  timeout 20s "$work/probe" valid > "$work/run.log" 2>&1 || {
    grep -Ex 'V737_CONTEXT_FAULT kind=[1-9] line=[0-9]{1,4} stage=[0-5] witness=[0-4] visits=[0-9]{1,3} outer=[0-9]{1,2} back_polls=[0-9]{1,3}|V762_EPILOGUE_INVALID reason=[1-9] stage=[0-5] visits=[0-9]{1,3}|V737_CONTEXT_MISMATCH gpr=[0-9]{1,2} cr=[01] lr=[01] ctr=[01] xer=[01] srr0=[01] srr1=[01] gqr=[0-8] exception_state=[01]' "$work/run.log" || true
    echo "V737_NATIVE_EXECUTION failed=1";exit 1;
  }
  grep -Fx 'V762_OWNER_LIVE_EPILOGUE valid=8 original_dispatcher=8 scheduler_enable=8 reschedule=8 native_rfi=8 synthetic_resume=8 fallback=0 continuous_boot=0' "$work/run.log"
  rc=0
  timeout 20s "$work/probe" switch > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V737_SWITCH_REFUSAL guarded_tail=1 original_switch=0' "$work/run.log"
  rc=0
  timeout 20s "$work/probe" corrupt > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V762_CONTEXT_REFUSAL saved_frame_corruption=1' "$work/run.log"
  echo "V737_MODE mode=$mode valid=8 switch_refused=1 corrupt_refused=1"
done
