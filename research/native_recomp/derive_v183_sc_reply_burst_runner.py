#!/usr/bin/env python3
"""V183 eight original PPC call entries after authentic V182 IPC sender frontier."""
import argparse
from pathlib import Path
from derive_v182_sc_reply_burst_runner import derive as previous

OLD='python3 "$here/derive_v182_sc_reply_burst_harness.py"'
NEW='python3 "$here/derive_v183_sc_reply_burst_harness.py"'
FAIL="  echo 'V130_NATIVE_EXIT ok=0'"
DONE="echo 'V182_SC_BURST verified=1'"
ACK=r'^V183_ACK_MMIO_DEP phase=[01] acked=[01] submit=[01] first=[01] msg=[01] ctrl=[01] flags=[01] requests=[0-9]{1,2} calls=[0-8] addr=[0-9a-f]{1,8}$'
DEP=r'^V183_IRQ_DEP phase=[01] submit=[01] dispatch=[01] ipc=[01] prior=[01] tracked=[01] masked=[01] mapped=[01] status=[0-9]{1,3} calls=[0-8] pc=[0-9a-f]{1,8} lr=[0-9a-f]{1,8}$'
SECOND_MSG=r'^V183_SECOND_MSG phase=1 prior=[01] idle=[01] aligned=[01] mapped=[01] known=[01] open=[01] read=[01] ioctl=[01] calls=[0-8]$'
SECOND_CTRL=r'^V183_SECOND_CTRL phase=1 prior=[01] msg=[01] wire=[01] clear=[01] x1=[01] calls=[0-8]$'
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
        +'  grep -E "'+TRACE+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+DEP+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+ACK+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+SECOND_MSG+'" "$work/private-native.log" | sort -u || true\n'
        +'  grep -E "'+SECOND_CTRL+'" "$work/private-native.log" | sort -u || true\n'+FAIL,1)
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
