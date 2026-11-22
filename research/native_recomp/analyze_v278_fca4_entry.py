#!/usr/bin/env python3
"""V278 private original Wii NAND callback entry census (16 trial bound).

Only aggregate sanitized guest entry counts. Inherited V269 separately
verifies the same 16 64-call original-code windows and zero SC writes.
"""
import argparse
from pathlib import Path
import re
import sys

N=16
ENTER=re.compile(
    r"^V278_FCA4_ENTRY n=([1-9][0-9]{0,2}) phase=([01]) cb=([01]) "
    r"nand=([01]) child=([01]) sc=([0-9]{1,3}) guest=([01]) "
    r"inst=([0-9]{1,18})$"
)
END=re.compile(
    r"^V278_SC_CALL_WINDOW pre=([0-9]{1,3}) "
    r"post=([0-9]{1,3}) events=([0-9]{1,3})$"
)
ERRORS={"malformed_event","malformed_end","wrong_event_order",
        "invalid_status","non_guest","nonmonotonic_inst",
        "phase_regression","invalid_event_counts","wrong_trial_count",
        "unterminated_trial"}

def parse(log:str)->list[tuple[tuple[int,int,int,int,int,int],...]]:
    trials=[]
    active=[]
    last_inst=0
    last_phase=0
    for line in log.splitlines():
        if line.startswith("V278_FCA4_ENTRY "):
            m=ENTER.fullmatch(line)
            if not m:raise ValueError("malformed_event")
            n,phase,cb,nand,child,sc,guest,inst=map(int,m.groups())
            if n!=len(active)+1 or n>256:
                raise ValueError("wrong_event_order")
            if sc>255:raise ValueError("invalid_status")
            if guest!=1:raise ValueError("non_guest")
            if active and inst<last_inst:raise ValueError("nonmonotonic_inst")
            if active and phase<last_phase:raise ValueError("phase_regression")
            active.append((phase,cb,nand,child,sc,inst))
            last_inst=inst
            last_phase=phase
        elif line.startswith("V278_SC_CALL_WINDOW "):
            m=END.fullmatch(line)
            if not m:raise ValueError("malformed_end")
            pre,post,events=map(int,m.groups())
            if (events!=len(active) or
                pre!=sum(phase==0 for phase,*_ in active) or
                post!=sum(phase==1 for phase,*_ in active)):
                raise ValueError("invalid_event_counts")
            trials.append(tuple(active))
            active=[]
            last_inst=last_phase=0
            if len(trials)>N:raise ValueError("wrong_trial_count")
    if active:raise ValueError("unterminated_trial")
    if len(trials)!=N:raise ValueError("wrong_trial_count")
    return trials

def summarize(trials:list[tuple[tuple[int,int,int,int,int,int],...]])->str:
    if len(trials)!=N:raise ValueError("wrong_trial_count")
    patterns=[tuple((phase,cb,nand,child,sc)
                    for phase,cb,nand,child,sc,_ in trial) for trial in trials]
    all_entries=[e for trial in trials for e in trial]
    return (
        f"V278_FCA4_CENSUS trials={N} frontier=64 "
        f"stable={int(len(set(patterns))==1)} distinct={len(set(patterns))} "
        f"entries={len(all_entries)} min_trial={min(map(len,trials))} "
        f"max_trial={max(map(len,trials))} "
        f"pre={sum(e[0]==0 for e in all_entries)} "
        f"post={sum(e[0]==1 for e in all_entries)} "
        f"child={sum(e[3] for e in all_entries)} "
        f"sc1={sum(e[4]==1 for e in all_entries)} "
        f"sc3={sum(e[4]==3 for e in all_entries)} "
        f"callback={sum(e[1] for e in all_entries)} "
        f"nand={sum(e[2] for e in all_entries)}"
    )

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_native_log",type=Path)
    a=p.parse_args()
    try: print(summarize(parse(a.private_native_log.read_text(
        encoding="utf-8",errors="replace"))))
    except (OSError,ValueError) as exc:
        reason=str(exc)
        if reason not in ERRORS:reason="input_error"
        print("V278_ENTRY_ERROR reason="+reason,file=sys.stderr)
        return 1
    return 0

if __name__=="__main__":
    sys.exit(main())
