#!/usr/bin/env bash
# Owner-private authentic Wii system-call vector AOT native execution regression.
set -euo pipefail
if (( $# != 2 )); then
  printf 'Usage: bash %s ISOLATED_NWII_ROOT OWNER_WII_DOL\n' "$0" >&2
  exit 2
fi
root="$(cd "$1" && pwd)"
owner="$(realpath "$2")"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cxx="${CXX:-g++}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
# Source-only, fail-closed compatibility patches; no proprietary code touched.
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
if ! grep -q 'uint32_t hid4 = 0;' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  python3 "$here/apply_perf_sprs_v29.py" "$root"
  python3 "$here/test_perf_patch_guards_v29.py" "$root"
  python3 "$here/apply_hid4_fp_v30.py" "$root"
  python3 "$here/test_hid4_patch_guards_v30.py" "$root"
fi
if grep -q 'std::array<uint32_t, 256> guest_flush_lines{};' "$root/nWiiRuntime/include/runtime/cpu_context.h"; then
  # Fully patched V44 requires exact cache-emitter anchors as well.
  python3 - "$root" "$here" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1]);sys.path.insert(0,sys.argv[2])
from apply_cache_events_v43 import EMITTER,EMIT_AFTER,ISYNC_AFTER
from apply_cache_trace_v44 import FILE,NEW
ctx=(root/FILE).read_text();emitter=(root/EMITTER).read_text()
if any(ctx.count(x)!=1 for x in NEW) or emitter.count(EMIT_AFTER)!=1 or emitter.count(ISYNC_AFTER)!=1:
    raise SystemExit('V45 rejected partially installed cache runtime/emitter')
print('PASS: V45 existing cache runtime/emitter source revision validated')
PY
else
  python3 "$here/apply_cache_events_v43.py" "$root"
  python3 "$here/test_cache_patch_guards_v43.py" "$root"
fi
python3 "$here/apply_cache_trace_v44.py" "$root"
python3 "$here/test_cache_trace_guards_v44.py"
python3 "$here/make_osinit_systemcall_v45.py" "$owner" "$work/owner_private.dol"
inc=( -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" )
"$cxx" -std=c++20 -O0 -Wall -Wextra -Wno-sign-compare -Wno-unused-variable "${inc[@]}" \
  "$here/generate_osinit_systemcall_v45.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" \
  "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" \
  "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" \
  "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
mkdir "$work/generated"
"$work/generator" "$work/owner_private.dol" "$work/generated"
python3 "$here/test_osinit_guards_v45.py" "$owner" "$work/generator"
flags=( -O2 )
if [[ "${V45_SANITIZE:-0}" == 1 ]]; then
  flags=( -O0 -g0 -fsanitize=address,undefined -fno-omit-frame-pointer )
fi
"$cxx" -std=c++20 "${flags[@]}" -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
  -I"$root/nWiiRuntime/include" \
  "$here/test_osinit_systemcall_v45.cpp" \
  "$work/generated/output.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" -o "$work/native"
"$work/native" "$work/owner_private.dol"
