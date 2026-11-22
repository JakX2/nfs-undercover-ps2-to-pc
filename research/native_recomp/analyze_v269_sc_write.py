#!/usr/bin/env python3
"""V269: classify original guest SYSCONF pre-stores in 16 bounded trials.

The MMU observer runs before any original guest write. Raw byte events
remain owner-private; only aggregate before/next value categories leave CI.
"""
import argparse
from pathlib import Path
import re
import sys

N=16
WRITE=re.compile(
    r"^V269_SC_WRITE n=([1-9][0-9]{0,2}) before=([0-9]{1,3}) "
    r"next=([0-9]{1,3}) width=8 guest=([01]) inst=([0-9]{1,18})$"
)
END=re.compile(
    r"^V260_CALL_FRONTIER guest=1 coherent=1 mapped=1 "
    r"calls=64 sc=1 pc=805265d4 lr=8052f92c$"
)
ERRORS={"invalid_marker","wrong_order","invalid_byte","invalid_guest",
        "instruction_regression","incomplete_window","wrong_trials"}


def parse(log:str)->list[tuple[tuple[int,int,int],...]]:
    trials=[]
    active=[]
    last_inst=0
    for line in log.splitlines():
        if line.startswith("V269_SC_WRITE "):
            m=WRITE.fullmatch(line)
            if not m:raise ValueError("invalid_marker")
            n,before,nxt,guest,inst=map(int,m.groups())
            if n!=len(active)+1 or n>512:raise ValueError("wrong_order")
            if before>255 or nxt>255:raise ValueError("invalid_byte")
            if guest!=1:raise ValueError("invalid_guest")
            if active and inst<last_inst:raise ValueError("instruction_regression")
            active.append((before,nxt,inst))
            last_inst=inst
        elif line.startswith("V260_CALL_FRONTIER "):
            if not END.fullmatch(line):raise ValueError("invalid_marker")
            trials.append(tuple(active))
            active=[]
            last_inst=0
            if len(trials)>N:raise ValueError("wrong_trials")
    if active:raise ValueError("incomplete_window")
    if len(trials)!=N:raise ValueError("wrong_trials")
    return trials


def summarize(trials:list[tuple[tuple[int,int,int],...]])->str:
    if len(trials)!=N:raise ValueError("wrong_trials")
    signatures=[tuple((a,b) for a,b,_ in t) for t in trials]
    events=[(a,b) for t in trials for a,b,_ in t]
    return (
        f"V269_SC_WATCH trials={N} frontier=64 "
        f"stable={int(len(set(signatures))==1)} distinct={len(set(signatures))} "
        f"events={len(events)} min_trial={min(map(len,trials))} "
        f"max_trial={max(map(len,trials))} "
        f"changed={sum(a!=b for a,b in events)} "
        f"write_zero={sum(b==0 for _,b in events)} "
        f"write_one={sum(b==1 for _,b in events)} "
        f"write_other={sum(b not in (0,1) for _,b in events)} "
        f"one_to_one={sum(a==1 and b==1 for a,b in events)} "
        f"one_to_zero={sum(a==1 and b==0 for a,b in events)}"
    )


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_private_log",type=Path)
    a=p.parse_args()
    try:
        print(summarize(parse(a.owner_private_log.read_text(
            encoding="utf-8",errors="replace"))))
    except (OSError,ValueError) as exc:
        kind=str(exc)
        if kind not in ERRORS:kind="input_error"
        print("V269_WATCH_ERROR reason="+kind,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
