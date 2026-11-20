#!/usr/bin/env python3
"""V182 eight-call native burst from original authenticated V181 boundary."""
import argparse
from pathlib import Path
from derive_v181_sc_reply_next_runner import derive as previous

OLD='python3 "$here/derive_v181_sc_reply_next_harness.py"'
NEW='python3 "$here/derive_v182_sc_reply_burst_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V181_SC_NEXT verified=1'"
DEP=r'^V182_V112_DEP phase=[01] op=[01] flush=[0-9]{1,2} sc=[0-9]{1,2} vector=[0-9]{1,2} order=[01] count=[01] calls=[0-8] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
FALLBACK=r'^V182_SC_FALLBACK phase=1 prior=[0-9]{1,2} vector=[0-9]{1,2} flush=[0-9]{1,2} burst=[0-8] mapped=[01] status=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
V114=r'^V182_V114_DEP phase=1 syscall=[0-9]{1,2} flush=[0-9]{1,2} cache=[0-9]{1,2} calls=[0-8] route=[01] flushed=[01] abi=[01] prior=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
VECTOR=r'^V182_CACHE_VECTOR entered=1 resume=[01] masked=[01] pc=80000c00 lr=[0-9a-f]{8}$'
PRE=r'^V182_CACHE_PRE phase=1 calls=[0-8] sc=[0-9]{1,2} vector=[0-9]{1,2} flush=[0-9]{1,2} lines=[01] hid4=[01] ee=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
AFTER=r'^V182_CACHE_AFTER pcok=[01] msr=[01] lr=[01] hid0=[01] hid4=[01] ctr=[01]$'
CACHE=r'^V182_CACHE_SC guest=1 vector=1 sc=1 status=[0-9]{1,3} pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
TRACE=r'^V182_SC_TRACE step=[1-8] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PATTERN=r'^V182_SC_BURST calls=[1-8] clean=[01] reply=[01] queue=[01] guest=[01] caller=[01] coherent=[01] mapped=[01] before=[0-9]{1,3} status=[0-9]{1,3} changed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'
PASS=r'^V182_SC_BURST calls=[1-8] clean=1 reply=1 queue=1 guest=1 caller=1 coherent=1 mapped=1 before=1 status=[0-9]{1,3} changed=[01] pc=[0-9a-f]{8} lr=[0-9a-f]{8}$'

def derive(source: str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(FAIL)!=1 or s.count(DONE)!=1:
        raise ValueError("V182 owner-original inherited runner source anchor differs")
    s=s.replace(OLD,NEW,1)
    s=s.replace(FAIL,
        '  grep -E "'+PATTERN+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+TRACE+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+DEP+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+FALLBACK+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+CACHE+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+PRE+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+AFTER+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+VECTOR+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+V114+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
    s=s.replace(DONE,DONE+f"""
grep -E '{PASS}' "$log" | sort -u
test "$(grep -Ec '{PASS}' "$log")" -eq 16
grep -E '{TRACE}' "$log" | sort -u
trace_count="$(grep -Ec '{TRACE}' "$log")"
test "$trace_count" -ge 16
test "$trace_count" -le 128
grep -E '{CACHE}' "$log" | sort -u
test "$(grep -Ec '{CACHE}' "$log")" -eq 16
grep -E '{VECTOR}' "$log" | sort -u
test "$(grep -Ec '{VECTOR}' "$log")" -eq 16
echo 'V182_CACHE_VECTOR verified=1'
echo 'V182_CACHE_SC verified=1'
echo 'V182_SC_BURST verified=1'
""",1)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
