#!/usr/bin/env python3
"""V248 regenerate authentic Wii callback functions from restored private DOL."""
import argparse
from pathlib import Path
from derive_v247_private_callback_restore_runner import derive as previous

DONE="echo 'V247_SC_PRIVATE_CALLBACK_RESTORE verified=1'"
PATTERN=r'^V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$'
PASS=r'^V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=1 cb_prologue=1 cb_bctrl=1 cb_link=1 cb_ctr=1 cb_return=1 isfs_entry=1 isfs_prologue=1 isfs_save=1 nand_entry=1 dispatch_cb=1 dispatch_isfs=1 dispatch_nand=1$'
BUILD='''# The prior owner test and original V247 restoration have both finished.
# Regenerate AOT C++ *privately* from the two restored genuine callbacks;
# never execute an unvalidated native callback or upload generated code.
mkdir "$work/v248-generated"
if "$work/generator" "$work/v247-restored.dol" "$work/v248-generated" owner > "$work/v248-generator.log" 2>&1; then
  echo 'V248_REGEN generator=1'
else
  echo 'V248_REGEN generator=0'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/audit_v245_generated_callback.py" "$owner" "$work/v247-restored.dol" "$work/v248-generated/output.cpp" > "$work/v248-scan.log" 2>&1; then
  if grep -E '^V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$' "$work/v248-scan.log"; then
    echo 'V248_REGEN scan=1'
  else
    echo 'V248_REGEN scan=0'
    exit 1
  fi
else
  grep -E '^V245_AOT_DIAG stage=(owner|fixture|generated|audit) kind=(read_failed|empty|validation|type)$' "$work/v248-scan.log" || true
  echo 'V248_REGEN scan=0'
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V248 original V247 private restoration stage changed")
    return s.replace(DONE,DONE+"""
"""+BUILD+f"""
test "$(grep -Ec '{PATTERN}' "$work/v248-scan.log")" -eq 1
grep -E '{PATTERN}' "$work/v248-scan.log" | sort -u
test "$(grep -Ec '{PASS}' "$work/v248-scan.log")" -eq 1
echo 'V248_SC_AUTH_AOT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
