#!/usr/bin/env python3
"""V249 compile and link privately regenerated authentic callback AOT.

The V248 callback/NAND restoration is generated and audited inside the
owner's ephemeral workspace. After V245 baseline owner-original execution
passes, compile that independently restored translated unit and link it
with the same original-free runtime/harness objects. DO NOT execute this
candidate until an independently checked guest-phase harness is ready.
"""
import argparse
from pathlib import Path
from derive_v245_sc_aot_map_runner import derive as previous

DONE="echo 'V248_SC_ORIGINAL_CALLBACK_AOT verified=1'"
ROW=r'^V249_AOT_LINK owner=1 restore=1 mapping=1 different=1 compiled=1 linked=1 executable=1$'
SCAN=r'^V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=1 cb_prologue=1 cb_bctrl=1 cb_link=1 cb_ctr=1 cb_return=1 isfs_entry=1 isfs_prologue=1 isfs_save=1 nand_entry=1 dispatch_cb=1 dispatch_isfs=1 dispatch_nand=1$'
STAGE=r'''# V249 private candidate: the reference baseline has already run
# its original Wii game code and verified V244's callback provenance.
# These separately restored guest functions must never be printed.
test -s "$work/private-v248.dol"
test -s "$work/generated-v248/output.cpp"
test -s "$work/generated/output.cpp"
test "$(grep -Ec 'V248_RESTORE owner=1 cb=1 nand=1 controls=1 reversible=1' "$work/v248-restore.log")" -eq 1
test "$(grep -Ec '^V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=1 cb_prologue=1 cb_bctrl=1 cb_link=1 cb_ctr=1 cb_return=1 isfs_entry=1 isfs_prologue=1 isfs_save=1 nand_entry=1 dispatch_cb=1 dispatch_isfs=1 dispatch_nand=1$' "$work/v248-aot.log")" -eq 1
if cmp -s "$work/generated/output.cpp" "$work/generated-v248/output.cpp"; then
  echo 'V249_AOT_DIAG stage=compare kind=identical'
  exit 1
fi
if g++ -std=c++20 -O2 -Wall -Wextra -Werror -Wno-type-limits -Wno-unused-label \
       -I"$V110_SOURCE_ROOT" -I"$root/nWiiRuntime/include" \
       -c "$work/generated-v248/output.cpp" -o "$work/v249-generated.o" \
       > "$work/v249-compile.log" 2>&1; then
  test -s "$work/v249-generated.o"
else
  python3 "$V110_SOURCE_ROOT/classify_v77_compile_failure.py" "$work/v249-compile.log" generated || true
  echo 'V249_AOT_DIAG stage=compile kind=failed'
  exit 1
fi
if g++ "$work/harness.o" "$work/v249-generated.o" "$work/loader.o" \
       -o "$work/v249-native" > "$work/v249-link.log" 2>&1; then
  test -s "$work/v249-native"
  test -x "$work/v249-native"
else
  python3 "$V110_SOURCE_ROOT/classify_v71_link_failure.py" "$work/v249-link.log" || true
  echo 'V249_AOT_DIAG stage=link kind=failed'
  exit 1
fi
echo 'V249_AOT_LINK owner=1 restore=1 mapping=1 different=1 compiled=1 linked=1 executable=1' | tee "$work/v249-proof.log"
'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V249 restored AOT mapping proof changed")
    return s.replace(DONE,DONE+"\n"+STAGE+f"""
test "$(grep -Ec '{ROW}' "$work/v249-proof.log")" -eq 1
echo 'V249_SC_AUTH_CALLBACK_LINK verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as file:
        file.write(derive(args.source.read_text(encoding="utf-8")))
