#!/usr/bin/env python3
"""V247 owner-local callback restoration after V245 baseline execution."""
import argparse
from pathlib import Path
from derive_v245_sc_aot_map_runner import derive as previous

DONE="echo 'V245_SC_AOT_MAP verified=1'"
PATTERN=r'^V247_CALLBACK_RESTORE auth=1 cb_safe=1 nand_safe=1 cb_changed=[01] nand_changed=[01] nop=[01] stub=[01] original=[01] restored=1 reversible=1$'
FAIL=r'^V247_RESTORE_FAIL stage=(auth|select|apply|verify|output) kind=(digest|range|foreign|install|span|header|reverse|exists|io|other)$'
STAGE='''if python3 "$V110_SOURCE_ROOT/restore_v247_private_callbacks.py" "$owner" "$work/private.dol" "$work/v247-restored.dol" > "$work/v247-restore.log" 2>&1; then
  grep -E '^V247_CALLBACK_RESTORE auth=1 cb_safe=1 nand_safe=1 cb_changed=[01] nand_changed=[01] nop=[01] stub=[01] original=[01] restored=1 reversible=1$' "$work/v247-restore.log"
else
  grep -E '^V247_RESTORE_FAIL stage=(auth|select|apply|verify|output) kind=(digest|range|foreign|install|span|header|reverse|exists|io|other)$' "$work/v247-restore.log" || true
  echo 'V247_RESTORE result=failed'
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V247 authenticated V245 owner runner checkpoint changed")
    return s.replace(DONE,DONE+"""
"""+STAGE+f"""
test "$(grep -Ec '{PATTERN}' "$work/v247-restore.log")" -eq 1
grep -E '{PATTERN}' "$work/v247-restore.log" | sort -u
echo 'V247_SC_PRIVATE_CALLBACK_RESTORE verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
