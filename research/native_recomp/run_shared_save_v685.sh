#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$1" && pwd)"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
work="$(mktemp -d)"
trap 'rm -rf -- "$work"' EXIT
python3 "$here/apply_verified_elf_spans_v6.py" "$root"
python3 "$here/apply_function_root_v443.py" "$root"
python3 "$here/apply_nonsplit_dispatch_v15.py" "$root"
python3 "$here/apply_exact_dispatch_v445.py" "$root"
python3 "$here/apply_syscall_pc_v26.py" "$root"
python3 "$here/apply_native_tick_v438.py" "$root"
PYTHONPATH="$here" python3 - "$root" <<'PY'
import sys
from pathlib import Path
from apply_si_roots_v669 import apply,TEST_SPANS
apply(Path(sys.argv[1]),TEST_SPANS,0x8000410c)
PY
inc=(-I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include")
g++ -std=c++20 -O2 "${inc[@]}" "$here/generate_shared_save_v685.cpp" \
  "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" \
  "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" -o "$work/generator"
for mode in nonsplit split; do
  mkdir "$work/$mode"
  "$work/generator" "$work/$mode" "$mode"
  PYTHONPATH="$here" python3 - "$work/$mode" <<'PY'
import sys
from pathlib import Path
from prepare_v680_si_helper import patch_helper,exact_function,verify_direct
from prepare_v625_ipc_client import audit_native
root=Path(sys.argv[1]);p=0x80004100;t=p+12
words=tuple(0x900b0000|(r<<21)|((-4*(32-r))&0xffff) for r in range(17,32))+(0x4e800020,)
sources=[f.read_text() for f in root.glob('*.cpp')]
matches=[s for s in sources if f'void func_{t:X}(CPUContext& ctx) {{' in s]
assert len(matches)==1
_,seen=patch_helper(matches[0],t,words)
main=(root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')).read_text()
# Non-split output contains function-local resume switches as well.
# The outer dispatcher audit must not confuse an interior goto with a root.
outer=main[main.index('extern "C" void run_game('):]
assert audit_native([exact_function(matches[0],t)],outer,seen)==16
calls=[s for s in sources if 'loc_80004008: ;' in s]
assert len(calls)==1
verify_direct(calls[0],0x80004008,t)
print('V685_SHARED_ALIAS_AUDIT labels=16 exact_root=1 direct_edge=1')
PY
  g++ -std=c++20 -O1 -fsanitize=address,undefined -Wall -Wextra -Werror -Wno-unused-label \
    -fno-pie -no-pie -I"$root/nWiiRuntime/include" "$here/test_shared_save_v685.cpp" "$work/$mode"/*.cpp -o "$work/probe"
  "$work/probe"
done
