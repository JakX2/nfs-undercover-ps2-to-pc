#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)";dol="$(realpath "$2")";elf="$(realpath "$3")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
umask 077
ulimit -c 0
python3 "$here/prepare_owner_transfer_v765.py" "$dol" "$elf" "$work/owner_transfer_input.h"
for patch in apply_verified_elf_spans_v6 apply_function_root_v443 apply_nonsplit_dispatch_v15 apply_exact_dispatch_v445 apply_native_tick_v438 apply_syscall_pc_v26; do
  python3 "$here/$patch.py" "$root" > "$work/patch.log" 2>&1 || { echo "V765_EMITTER_PATCH failed=1";exit 1; }
done
python3 "$here/prepare_owner_transfer_v765.py" "$dol" "$elf" "$root" --patch-analyzer
inc=(-I"$work" -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_owner_transfer_v765.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
 "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
 "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator" > "$work/build.log" 2>&1 || { echo "V765_TRANSLATOR_BUILD failed=1";exit 1; }
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode" > "$work/generate.log" 2>&1 || { echo "V765_TRANSLATION failed=1";exit 1; }
  python3 "$here/prepare_owner_transfer_v765.py" "$dol" "$elf" "$work/$mode" --install
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label -fno-pie -no-pie \
    -I"$work" -I"$here" -I"$root/nWiiRuntime/include" "$here/test_owner_transfer_v765.cpp" "$work/$mode"/*.cpp -o "$work/probe" > "$work/build.log" 2>&1 || { python3 "$here/diagnose_transfer_build_v768.py" "$work/build.log";echo "V765_NATIVE_BUILD failed=1";exit 1; }
  timeout 20s "$work/probe" valid > "$work/run.log" 2>&1 || {
    grep -Ex 'V765_TRANSFER_FAULT kind=[1-8] line=[0-9]{1,4} entries=[0-6] visits=[0-9]{1,3} busy=[01] reads=[0-9]{1,3} writes=[0-9]{1,3} follow=[0-3] reason=[0-5]' "$work/run.log" || true
    echo "V765_NATIVE_EXECUTION failed=1";exit 1;
  }
  grep -Fx 'V765_OWNER_TRANSFER_AOT valid=8 idle=4 busy=4 native_requests=4 follow_on=4 fallback=0 continuous_boot=0' "$work/run.log"
  rc=0
  timeout 20s "$work/probe" corrupt > "$work/run.log" 2>&1 || rc=$?
  [[ "$rc" == 126 ]]
  grep -Fx 'V765_TRANSFER_REFUSAL mask_corruption=1' "$work/run.log"
  echo "V765_MODE mode=$mode valid=8 corrupt_refused=1"
done
