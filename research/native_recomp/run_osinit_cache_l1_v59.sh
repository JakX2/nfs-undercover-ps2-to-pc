#!/usr/bin/env bash
# V59: bounded owner-original OSInit -> __OSCacheInit original L1 enable path.
# Removes generated game-code C++, sliced private DOL and executables on exit.
set -euo pipefail
if (( $# != 2 )); then
  echo "Usage: bash $0 ISOLATED_NWII_ROOT OWNER_ORIGINAL_WII_DOL" >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
owner="$(realpath "$2")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
python3 - "$owner" <<'PY'
import hashlib,sys
from pathlib import Path
expected='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()!=expected:
    raise SystemExit('V59 rejected original owner game DOL SHA-256')
print('PASS: V59 original Wii DOL SHA-256 matched')
PY
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
if ! grep -q 'uint32_t hid4 = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 "$here/apply_perf_sprs_v29.py" "$root"
  python3 "$here/test_perf_patch_guards_v29.py" "$root"
  python3 "$here/apply_hid4_fp_v30.py" "$root"
  python3 "$here/test_hid4_patch_guards_v30.py" "$root"
fi
if grep -q 'std::array<uint32_t, 256> guest_flush_lines{};' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 - "$root" "$here" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]);sys.path.insert(0,sys.argv[2])
from apply_cache_events_v43 import EMITTER,EMIT_AFTER,ISYNC_AFTER
from apply_cache_trace_v44 import FILE,NEW
ctx=(root/FILE).read_text();emitter=(root/EMITTER).read_text()
if any(ctx.count(x)!=1 for x in NEW) or emitter.count(EMIT_AFTER)!=1 or emitter.count(ISYNC_AFTER)!=1:
    raise SystemExit('V59 rejected partially installed cache trace/runtime')
print('PASS: V59 existing cache runtime/emitter source revision validated')
PY
else
  python3 "$here/apply_cache_events_v43.py" "$root"
  python3 "$here/test_cache_patch_guards_v43.py" "$root"
fi
python3 "$here/apply_cache_trace_v44.py" "$root"
python3 "$here/test_cache_trace_guards_v44.py"
python3 "$here/make_osinit_cache_l1_v59.py" "$owner" "$work/private.dol"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O0 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_osinit_cache_l1_v59.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"
"$work/generator" "$work/private.dol" "$work/generated"
python3 "$here/test_osinit_guards_v59.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V59_SANITIZE:-0}" == 1 ]]; then
  flags=( -O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_osinit_cache_l1_v59.cpp" \
  "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native"
if ! "$work/native" "$work/private.dol" >"$work/native.log" 2>&1; then
  tail -80 "$work/native.log" >&2
  exit 1
fi
grep '^PASS:' "$work/native.log"
