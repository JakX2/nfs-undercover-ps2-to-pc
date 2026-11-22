#!/usr/bin/env python3
"""V262: flatten owner-native derivation while retaining V261 call proof."""
import argparse
from pathlib import Path
from derive_v260_ipc_ppcmsg_boundary_runner import derive as previous
from derive_v261_guest_call_census_runner import APPEND as V261_APPEND

OLD='python3 "$V110_SOURCE_ROOT/derive_v260_ipc_ppcmsg_boundary_harness.py"'
NEW='python3 "$V110_SOURCE_ROOT/derive_v262_ipc_state_harness.py"'
DONE="echo 'V260_SC_POSTIPC_EVENT verified=1'"
EXTRA=V261_APPEND+'''
python3 "$V110_SOURCE_ROOT/analyze_v262_ipc_state.py" "$work/v250-native.log"
echo 'V262_IPC_STATE verified=1'
'''

def derive(source:str)->str:
    s=previous(source)
    if s.count(OLD)!=1 or s.count(DONE)!=1:
        raise ValueError("V262 inherited V260 owner-native runner changed")
    return s.replace(OLD,NEW,1).replace(DONE,DONE+EXTRA,1)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
