#!/usr/bin/env python3
"""V253 owner-local classification of the one non-callback AOT change.

The authenticated original changes in _isfsFuncCb and nandOpenCallback
were independently regenerated and linked (V248-V251). V251 observed
one additional changed generated function. This tool identifies only
its text PC and whether it lies within/next to the restored callback
ranges or is the parser's final function. Never output the actual PPC
code, translated C++ body, owner pathname or instruction bytes.
"""
import argparse
from pathlib import Path
from audit_v245_generated_callback import SPANS, CALLS
from audit_v251_callback_generated_diff import functions, CONTROLS, TARGETS

def classify(before:str,after:str)->str:
    old=functions(before);new=functions(after)
    if not old or not new or not TARGETS.issubset(old) or not TARGETS.issubset(new):
        raise ValueError("V253 authenticated original callback AOT entries missing")
    if not all(k in old and k in new and old[k]==new[k] for k in CONTROLS.values()):
        raise ValueError("V253 control functions unexpectedly changed")
    if not all(old[k]!=new[k] for k in TARGETS):
        raise ValueError("V253 callback bodies were not restored")
    shared=set(old)&set(new)
    changed=sorted(k for k in (shared-TARGETS) if old[k]!=new[k])
    count=min(len(changed),999999)
    single=len(changed)==1
    pc=changed[0] if single else 0
    def in_span(key:str)->bool:
        start,size=SPANS[key]
        return single and start<=pc<start+size
    def adjacent(key:str)->bool:
        start,size=SPANS[key]
        return single and start-0x100<=pc<start+size+0x100
    last=single and (pc==next(reversed(old)) or pc==next(reversed(new)))
    same_len=single and len(old[pc])==len(new[pc])
    return ("V253_AOT_OTHER parsed=1 count="+str(count)+
            " pc="+f"{pc:08x}"+
            " in_cb="+str(int(in_span("cb")))+
            " in_nand="+str(int(in_span("nand")))+
            " near_cb="+str(int(adjacent("cb")))+
            " near_nand="+str(int(adjacent("nand")))+
            " last="+str(int(last))+
            " same_len="+str(int(same_len))+
            " controls=1 restored=1")

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_baseline_cpp",type=Path)
    p.add_argument("private_restored_cpp",type=Path)
    a=p.parse_args()
    try:
        prior=a.private_baseline_cpp.read_text(encoding="utf-8",errors="replace")
        current=a.private_restored_cpp.read_text(encoding="utf-8",errors="replace")
        row=classify(prior,current)
    except (OSError,ValueError,IndexError):
        print("V253_AOT_OTHER_DIAG reason=unavailable")
        return 1
    print(row)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
