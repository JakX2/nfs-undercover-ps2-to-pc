#!/usr/bin/env python3
"""V245 verified original Wii fixture and emitted callback AOT dispatch audit."""
import argparse
from pathlib import Path
from derive_v244_sc_callback_link_runner import derive as previous

DONE="echo 'V244_SC_CALLBACK_LINK verified=1'"
MARKERS=("echo 'V104_STAGE generation_complete'",
         "echo 'V79_STAGE generation_complete'")
PATTERN=r'^V245_AOT_MAP owner=1 fixture_cb=[01] fixture_isfs=[01] fixture_nand=[01] fixture_ipc=[01] cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$'
V247_ROW=r'^V247_FIXTURE owner=1 cb_same=[0-9]{1,2} cb_nop=[0-9]{1,2} cb_sc=[0-9]{1,2} cb_blr=[0-9]{1,2} cb_zero=[0-9]{1,2} cb_other=[0-9]{1,2} cb_placeholder=[01] nand_same=[0-9]{1,2} nand_nop=[0-9]{1,2} nand_sc=[0-9]{1,2} nand_blr=[0-9]{1,2} nand_zero=[0-9]{1,2} nand_other=[0-9]{1,2} nand_placeholder=[01]$'
CENSUS='''if python3 "$V110_SOURCE_ROOT/audit_v247_fixture_placeholders.py" "$owner" "$work/private.dol" > "$work/v247-fixture.log" 2>&1; then
  grep -E '^V247_FIXTURE owner=1 cb_same=[0-9]{1,2} cb_nop=[0-9]{1,2} cb_sc=[0-9]{1,2} cb_blr=[0-9]{1,2} cb_zero=[0-9]{1,2} cb_other=[0-9]{1,2} cb_placeholder=[01] nand_same=[0-9]{1,2} nand_nop=[0-9]{1,2} nand_sc=[0-9]{1,2} nand_blr=[0-9]{1,2} nand_zero=[0-9]{1,2} nand_other=[0-9]{1,2} nand_placeholder=[01]$' "$work/v247-fixture.log" | sort -u
else
  grep -Fx 'V247_FIXTURE_DIAG result=failed' "$work/v247-fixture.log" || true
  echo 'V247_FIXTURE result=failed'
  exit 1
fi'''
V248_ROW=r'^V248_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$'
V248_ORIGINAL=V248_ROW.replace("V248_AOT_MAP","V245_AOT_MAP")
CANDIDATE='''echo 'V248_STAGE entered=1'
if python3 "$V110_SOURCE_ROOT/restore_v248_original_callbacks.py" "$owner" "$work/private.dol" "$work/private-v248.dol" > "$work/v248-restore.log" 2>&1; then
  grep -Fx 'V248_RESTORE owner=1 cb=1 nand=1 controls=1 reversible=1' "$work/v248-restore.log"
else
  grep -Fx 'V248_RESTORE result=failed' "$work/v248-restore.log" || true
  echo 'V248_STAGE restore_failed=1'
  exit 1
fi
mkdir "$work/generated-v248"
if "$work/generator" "$work/private-v248.dol" "$work/generated-v248" owner > "$work/v248-generation.log" 2>&1; then
  echo 'V248_STAGE generator=1'
else
  echo 'V248_STAGE generator_failed=1'
  exit 1
fi
if python3 "$V110_SOURCE_ROOT/audit_v245_generated_callback.py" "$owner" "$work/private-v248.dol" "$work/generated-v248/output.cpp" > "$work/v248-aot.log" 2>&1; then
  if grep -E '^V245_AOT_MAP owner=1 fixture_cb=1 fixture_isfs=1 fixture_nand=1 fixture_ipc=1 cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$' "$work/v248-aot.log" | sed 's/^V245_AOT_MAP /V248_AOT_MAP /'; then
    echo 'V248_STAGE completed=1'
  else
    echo 'V248_STAGE map_mismatch=1'
    exit 1
  fi
else
  grep -E '^V245_AOT_DIAG stage=(owner|fixture|generated|audit) kind=(read_failed|empty|validation|type)$' "$work/v248-aot.log" | sort -u || true
  echo 'V248_STAGE audit_failed=1'
  exit 1
fi'''
AUDIT='''echo 'V245_STAGE entered=1'
if python3 "$V110_SOURCE_ROOT/audit_v245_generated_callback.py" "$owner" "$work/private.dol" "$work/generated/output.cpp" > "$work/v245-aot.log" 2>&1; then
  if grep -E '^V245_AOT_MAP owner=1 fixture_cb=[01] fixture_isfs=[01] fixture_nand=[01] fixture_ipc=[01] cb_entry=[01] cb_prologue=[01] cb_bctrl=[01] cb_link=[01] cb_ctr=[01] cb_return=[01] isfs_entry=[01] isfs_prologue=[01] isfs_save=[01] nand_entry=[01] dispatch_cb=[01] dispatch_isfs=[01] dispatch_nand=[01]$' "$work/v245-aot.log"; then
    echo 'V245_STAGE completed=1'
  else
    echo 'V245_AOT_DIAG stage=record kind=mismatch'
    exit 1
  fi
else
  grep -E '^V245_AOT_DIAG stage=(owner|fixture|generated|audit) kind=(read_failed|empty|validation|type)$' "$work/v245-aot.log" | sort -u || true
  echo 'V245_STAGE failed=1'
  echo 'V245_AOT_MAP result=failed'
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    markers=[item for item in MARKERS if s.count(item)==1]
    if len(markers)!=1 or s.count(DONE)!=1:
        raise ValueError("V245 generation checkpoint or prior proof changed")
    s=s.replace(markers[0],markers[0]+"\n"+AUDIT+"\n"+CENSUS+"\n"+CANDIDATE,1)
    return s.replace(DONE,DONE+f"""
test "$(grep -Ec '{PATTERN}' "$work/v245-aot.log")" -eq 1
grep -E '{PATTERN}' "$work/v245-aot.log" | sort -u
echo 'V245_SC_AOT_MAP verified=1'
test "$(grep -Ec '{V247_ROW}' "$work/v247-fixture.log")" -eq 1
echo 'V247_SC_FIXTURE_CLASS verified=1'
test "$(grep -Ec '^V248_RESTORE owner=1 cb=1 nand=1 controls=1 reversible=1$' "$work/v248-restore.log")" -eq 1
test "$(grep -Ec '{V248_ORIGINAL}' "$work/v248-aot.log")" -eq 1
echo 'V248_SC_ORIGINAL_CALLBACK_AOT verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
