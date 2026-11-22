#!/usr/bin/env python3
"""V281 private original Wii NAND call to 0x8051E150, 16 bounded trials."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys

N=16
ENTER=re.compile(
    r"^V281_SERVICE_ENTRY n=([1-9][0-9]{0,2}) phase=([01]) "
    r"child=([01]) sc=([0-9]{1,3}) guest=([01]) inst=([0-9]{1,18})$"
)
END=re.compile(
    r"^V281_SERVICE_WINDOW pre=([0-9]{1,3}) post=([0-9]{1,3}) "
    r"child=([0-9]{1,3}) entries=([0-9]{1,3})$"
)
ERRORS={"wrong_trials","bad_event","bad_window","seq","guest",
        "status","inst_order","phase_order","inconsistent_window",
        "unterminated"}

def parse(log:str)->list[tuple[tuple[int,int,int,int],...]]:
    trials=[]
    current=[]
    previous_inst=0
    prev_phase=0
    for line in log.splitlines():
        if line.startswith("V281_SERVICE_ENTRY "):
            m=ENTER.fullmatch(line)
            if not m:raise ValueError("bad_event")
            n,phase,child,sc,guest,inst=map(int,m.groups())
            if n!=len(current)+1 or n>256:raise ValueError("seq")
            if guest!=1:raise ValueError("guest")
            if sc>255:raise ValueError("status")
            if current and inst<previous_inst:raise ValueError("inst_order")
            if current and phase<prev_phase:raise ValueError("phase_order")
            current.append((phase,child,sc,inst))
            previous_inst=inst
            prev_phase=phase
        elif line.startswith("V281_SERVICE_WINDOW "):
            m=END.fullmatch(line)
            if not m:raise ValueError("bad_window")
            pre,post,child,entries=map(int,m.groups())
            if (len(current)!=entries or
                pre!=sum(x[0]==0 for x in current) or
                post!=sum(x[0]==1 for x in current) or
                child!=sum(x[1] for x in current)):
                raise ValueError("inconsistent_window")
            trials.append(tuple(current))
            current=[]
            previous_inst=prev_phase=0
            if len(trials)>N:raise ValueError("wrong_trials")
    if current:raise ValueError("unterminated")
    if len(trials)!=N:raise ValueError("wrong_trials")
    return trials

def summary(trials:list[tuple[tuple[int,int,int,int],...]])->str:
    if len(trials)!=N:raise ValueError("wrong_trials")
    signatures=[tuple((phase,child,sc) for phase,child,sc,_ in trial)
                for trial in trials]
    events=[entry for trial in trials for entry in trial]
    return (
        f"V281_NAND_SERVICE trials={N} frontier=64 "
        f"stable={int(len(set(signatures))==1)} "
        f"distinct={len(set(signatures))} entries={len(events)} "
        f"min_trial={min(map(len,trials))} max_trial={max(map(len,trials))} "
        f"pre={sum(x[0]==0 for x in events)} "
        f"post={sum(x[0]==1 for x in events)} "
        f"child={sum(x[1] for x in events)} "
        f"sc1={sum(x[2]==1 for x in events)} "
        f"sc3={sum(x[2]==3 for x in events)}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_private_log",type=Path)
    a=p.parse_args()
    try: print(summary(parse(a.owner_private_log.read_text(
        encoding="utf-8",errors="replace"))))
    except (OSError,ValueError) as exc:
        reason=str(exc)
        if reason not in ERRORS:reason="input_error"
        print("V281_SERVICE_ERROR reason="+reason,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
