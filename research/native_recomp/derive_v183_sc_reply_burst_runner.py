#!/usr/bin/env python3
"""V183 eight original PPC call entries after authentic V182 IPC sender frontier."""
import argparse
from pathlib import Path
from derive_v182_sc_reply_burst_runner import derive as previous

OLD='python3 "$here/derive_v182_sc_reply_burst_harness.py"'
NEW='python3 "$here/derive_v183_sc_reply_burst_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V182_SC_BURST verified=1'"
TRACE=r'^V183_SC_TRACE step=[1-8] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PATTERN=r'^V183_SC_BURST calls=[1-8] clean=[01] reply=[01] queue=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] before=[0-9]{1,3} status=[0-9]{1,3} changed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V183_SC_BURST calls=[1-8] clean=1 reply=1 queue=1 guest=1 caller=1 coherent=1 mapped=1 before=1 status=[0-9]{1,3} changed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V183 inherited owner-native runner source guards differ")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+TRACE+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -E '{TRACE}' "$log" | sort -u
trace_count="$(grep -Ec '{TRACE}' "$log")"
test "$trace_count" -ge 16
test "$trace_count" -le 128
echo 'V183_SC_BURST verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
