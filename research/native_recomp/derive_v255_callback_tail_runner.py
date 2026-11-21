#!/usr/bin/env python3
"""V255 prove the extra last AOT difference is outside native function code."""
import argparse
from pathlib import Path
from derive_v253_callback_other_runner import derive as previous

DONE="echo 'V253_SC_AOT_OTHER verified=1'"
PATTERN=r'^V255_AOT_TAIL parsed=1 last=1 pc=[0-9a-f]{8} body_same=[01] tail_diff=[01] controls=1 extras=1$'
PASS=r'^V255_AOT_TAIL parsed=1 last=1 pc=8054b4b4 body_same=1 tail_diff=1 controls=1 extras=1$'
STAGE='''# Parse only private regenerated C++ locally; never publish AOT contents.
if python3 "$V110_SOURCE_ROOT/audit_v255_callback_tail.py" \
       "$work/generated/output.cpp" "$work/generated-v248/output.cpp" \
       > "$work/v255-tail.log" 2>&1; then
  grep -E '^V255_AOT_TAIL parsed=1 last=1 pc=[0-9a-f]{8} body_same=[01] tail_diff=[01] controls=1 extras=1$' "$work/v255-tail.log" | sort -u
else
  grep -Fx 'V255_AOT_TAIL_DIAG reason=unavailable' "$work/v255-tail.log" || true
  exit 1
fi'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(DONE)!=1:
        raise ValueError("V255 authenticated V253 extra AOT classification missing")
    return s.replace(DONE,DONE+"\n"+STAGE+f"""
test "$(grep -Ec '{PATTERN}' "$work/v255-tail.log")" -eq 1
test "$(grep -Ec '{PASS}' "$work/v255-tail.log")" -eq 1
echo 'V255_SC_AOT_TAIL verified=1'
""",1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
