#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
python3 "$here/test_mtmsr_resume_patch_v74.py"
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_mtmsr_resume_v74.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/apply_native_lowmem_v63.py" "$root"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_irq_roundtrip_v78.cpp" \
    "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
    "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
    "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
for mode in nonsplit split; do
    mkdir "$work/$mode"
    "$work/generator" "$work/$mode" "$mode"
    g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label \
      -I"$root/nWiiRuntime/include" "$here/test_irq_roundtrip_v78.cpp" "$work/$mode"/*.cpp -o "$work/test"
    "$work/test"
done
