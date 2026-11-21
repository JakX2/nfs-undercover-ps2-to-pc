#!/usr/bin/env python3
"""V253 classify the additional changed original Wii AOT function only."""
import argparse
from pathlib import Path
from derive_v251_callback_generated_diff_runner import derive as previous

DONE="echo 'V251_SC_CALLBACK_DIFF verified=1'"
PATTERN=r'^V253_AOT_OTHER parsed=1 count=[0-9]{1,6} pc=[0-9a-f]{8} in_cb=[01] in_nand=[01] near_cb=[01] near_nand=[01] last=[01] same_len=[01] controls=1 restored=1$'
STAGE='''# Do not expose generated AOT C++ or original PPC instruction data.
if python3 "$V110_SOURCE_ROOT/audit_v253_callback_other.py" \
       "$work/generated/output.cpp" "$work/generated-v248/output.cpp" \
       > "$work/v253-other.log" 2>&1; then
  grep -E '^V253_AOT_OTHER parsed=1 count=[0-9]{1,6} pc=[0-9a-f]{8} in_cb=[01] in_nand=[01] near_cb=[01] near_nand=[01] last=[01] same_len=[01] controls=1 restored=1$' "$work/v253-other.log" | sort -u
else
  grep -Fx 'V253_AOT_OTHER_DIAG reason=unavailable' "$work/v253-other.log" || true
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V253 V251 owner-authenticated AOT diff boundary changed")
    return s.replace(DONE,DONE+"\n"+STAGE+f"""
test "$(grep -Ec '{PATTERN}' "$work/v253-other.log")" -eq 1
echo 'V253_SC_AOT_OTHER verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as f:
        f.write(derive(a.source.read_text(encoding="utf-8")))
