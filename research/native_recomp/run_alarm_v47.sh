#!/usr/bin/env bash
# Real Wii PowerPC alarm startup, translated by NWiiRecomp. Private source
# DOL and generated game C++ are deleted when this process exits.
set -euo pipefail
if (( $# != 2 )); then
  echo "Usage: $0 ISOLATED_NWII_ROOT OWNER_DOL" >&2; exit 2
fi
root="$(cd "$1" && pwd)"; owner="$(realpath "$2")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 - "$owner" <<'PY'
from pathlib import Path
import sys,hashlib
assert hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()=='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4', 'owner DOL mismatch'
PY
work="$(mktemp -d)"; trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/make_alarm_v47.py" "$owner" "$work/private.dol"
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O0 -g0 -Wno-unused-variable -Wno-sign-compare "${inc[@]}" \
 "$here/generate_alarm_v47.cpp" "$root/nWiiRuntime/src/core/loader.cpp" \
 "$root/nWiiAnalyzer/src/analyzer.cpp" "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
 "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" \
 "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/output"
"$work/generator" "$work/private.dol" "$work/output"
python3 "$here/test_alarm_guards_v47.py" "$owner" "$work/generator"
flags=(-O2)
if [[ "${V47_SANITIZE:-0}" == 1 ]]; then
 flags=(-O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer)
fi
g++ -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-unused-label \
 -I"$root/nWiiRuntime/include" \
 "$here/test_alarm_v47.cpp" "$work/output/output.cpp" \
 "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native"
"$work/native" "$work/private.dol"
