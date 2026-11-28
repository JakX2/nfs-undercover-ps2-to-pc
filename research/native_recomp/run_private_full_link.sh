#!/usr/bin/env bash
# Build the complete locally generated project without launching the game.
# All source, intermediate objects, binaries and detailed logs stay private.
set -euo pipefail
umask 077
if [[ $# -ne 2 ]]; then
  echo 'Usage: run_private_full_link.sh PRIVATE_GENERATED_DIR FRESH_PRIVATE_BUILD_DIR' >&2
  exit 2
fi
src="$(realpath "$1")"
build="$(realpath -m "$2")"
[[ -f "$src/CMakeLists.txt" && ! -e "$build" && ! -L "$build" ]] || {
  echo 'V415_FULL_LINK stage=input result=failed'; exit 1;
}
# Keep the build out of the generated tree and never replace existing files.
case "$build/" in "$src/"*) echo 'V415_FULL_LINK stage=input result=failed'; exit 1;; esac
# Older independent link callers retain the legacy counter policy.
# V572 explicitly selects guest-only V438 after patching its emitter.
dispatch_policy="${UNDERCOVER_WII_GUEST_ONLY_DISPATCH:-0}"
if [[ "$dispatch_policy" != 0 && "$dispatch_policy" != 1 ]]; then
  echo 'V415_FULL_LINK stage=policy result=failed'; exit 1
fi
mkdir -m 700 "$build"
echo 'V415_FULL_LINK stage=input result=passed'
if ! timeout --kill-after=10s 600s cmake -S "$src" -B "$build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Debug "-DCMAKE_CXX_FLAGS_DEBUG=-O0 -g0 -DUNDERCOVER_WII_GUEST_ONLY_DISPATCH=$dispatch_policy" \
    '-DCMAKE_C_FLAGS_DEBUG=-O0 -g0' -DCMAKE_RUNTIME_OUTPUT_DIRECTORY="$build/bin" \
    > "$build/configure-private.log" 2>&1; then
  echo 'V415_FULL_LINK stage=configure result=failed'; exit 1
fi
echo 'V415_FULL_LINK stage=configure result=passed'
# No optimizations or debug-info generation: prioritize a complete link
# over performance. The two-worker ceiling bounds peak compiler memory.
if ! python3 "$(dirname "$0")/run_native_link_progress_v1026.py" "$build"; then
  echo 'V415_FULL_LINK stage=build result=failed'; exit 1
fi
echo 'V415_FULL_LINK stage=build result=passed'
# Validate a nonempty x86-64 Linux ELF executable (ET_EXEC or PIE ET_DYN),
# not merely an object or library. Do not run the executable.
if ! python3 - "$build/bin/UndercoverWiiLocal" <<'PY' > "$build/verify-private.log" 2>&1
import os,struct,sys
from pathlib import Path
p=Path(sys.argv[1])
if not p.is_file() or p.is_symlink() or not os.access(p,os.X_OK):sys.exit(1)
with p.open('rb') as f: raw=f.read(64)
if len(raw)!=64 or raw[:7]!=b'\x7fELF\x02\x01\x01':sys.exit(1)
kind,machine,version,entry,phoff=struct.unpack_from('<HHIQQ',raw,16)
phentsize,phnum=struct.unpack_from('<HH',raw,54)
if kind not in (2,3) or machine!=62 or version!=1 or not entry or not phnum or phentsize!=56 or phoff<64 or phoff+phnum*phentsize>p.stat().st_size:sys.exit(1)
PY
then
  echo 'V415_FULL_LINK stage=verify result=failed'; exit 1
fi
echo 'V415_FULL_LINK stage=verify result=passed'
echo 'V415_FULL_LINK_GATE linked=1 platform=linux-x64 launch=0 boot_verified=0'
