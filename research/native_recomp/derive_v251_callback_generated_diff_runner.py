#!/usr/bin/env python3
"""V251 privately compare original callback-generated native AOT functions."""
import argparse
from pathlib import Path
from derive_v249_private_callback_native_link_runner import derive as previous

DONE="echo 'V249_SC_AUTH_CALLBACK_LINK verified=1'"
PATTERN=r'^V251_AOT_DIFF parsed=1 cb=[01] nand=[01] ipc=[01] isfs=[01] async=[01] changed=[0-9]{1,6} new=[0-9]{1,6} removed=[0-9]{1,6}$'
STAGE='''# Original Wii AOT files remain ephemeral and private.
if python3 "$V110_SOURCE_ROOT/audit_v251_callback_generated_diff.py"       "$work/generated/output.cpp" "$work/generated-v248/output.cpp"       > "$work/v251-diff.log" 2>&1; then
  grep -E '^V251_AOT_DIFF parsed=1 cb=[01] nand=[01] ipc=[01] isfs=[01] async=[01] changed=[0-9]{1,6} new=[0-9]{1,6} removed=[0-9]{1,6}$' "$work/v251-diff.log" | sort -u
else
  grep -Fx 'V251_AOT_DIFF_DIAG reason=unavailable' "$work/v251-diff.log" || true
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V251 private restored callback AOT link checkpoint missing")
    return s.replace(DONE,DONE+"\n"+STAGE+f"""
test "$(grep -Ec '{PATTERN}' "$work/v251-diff.log")" -eq 1
echo 'V251_SC_CALLBACK_DIFF verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    args=p.parse_args()
    with args.output.open("x",encoding="utf-8") as f:
        f.write(derive(args.source.read_text(encoding="utf-8")))
