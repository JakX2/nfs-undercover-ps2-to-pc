#!/usr/bin/env python3
"""V245 verified original Wii fixture and emitted callback AOT dispatch audit."""
import argparse
from pathlib import Path
from derive_v244_sc_callback_link_runner import derive as previous

DONE="echo 'V244_SC_CALLBACK_LINK verified=1'"
MARKERS=("echo 'V104_STAGE generation_complete'",
         "echo 'V79_STAGE generation_complete'")
PATTERN=r'^V245_AOT_MAP owner=1 fixture_cb=[01] fixture_isfs=[01] fixture_nand=[01] fixture_ipc=[01] cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$'
AUDIT='''if python3 "$V110_SOURCE_ROOT/audit_v245_generated_callback.py" "$owner" "$work/private.dol" "$work/generated/output.cpp" > "$work/v245-aot.log" 2>&1; then
  grep -E '^V245_AOT_MAP owner=1 fixture_cb=[01] fixture_isfs=[01] fixture_nand=[01] fixture_ipc=[01] cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$' "$work/v245-aot.log"
else
  grep -E '^V245_AOT_DIAG stage=(owner|fixture|generated|audit) kind=(read_failed|empty|validation|type)$' "$work/v245-aot.log" | sort -u || true
  echo 'V245_AOT_MAP result=failed'
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    markers=[item for item in MARKERS if s.count(item)==1]
    if len(markers)!=1 or s.count(DONE)!=1:
        raise ValueError("V245 generation checkpoint or prior proof changed")
    s=s.replace(markers[0],markers[0]+"\n"+AUDIT,1)
    return s.replace(DONE,DONE+f"""
test "$(grep -Ec '{PATTERN}' "$log")" -eq 1
grep -E '{PATTERN}' "$log" | sort -u
echo 'V245_SC_AOT_MAP verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
