#!/usr/bin/env python3
"""V255 classify only native function code versus trailing generated AOT data.

V253 owner-authenticated showed exactly one extra AOT diff at last
function 0x8054B4B4, outside either restored original callback span.
V251's parser extends the final function until EOF, so emitted tables
can be incorrectly counted as an unrelated changed function. Parse
the final C++ brace-balanced body, respecting comments/quoted braces,
and compare it separately from trailing source. All original bytes,
generated C++ and private filenames stay inside ephemeral owner CI.
Only a fixed bounded boolean/address row is publicly printed.
"""
import argparse
from pathlib import Path
from audit_v251_callback_generated_diff import functions, TARGETS, CONTROLS

def body_only(raw:str)->str:
    start=raw.find("{")
    if start<0:
        raise ValueError("V255 missing generated C++ function opening brace")
    depth=0
    state="code"
    i=start
    while i<len(raw):
        ch=raw[i]
        nxt=raw[i+1] if i+1<len(raw) else ""
        if state=="line":
            if ch=="\n":state="code"
        elif state=="block":
            if ch=="*" and nxt=="/":
                state="code";i+=1
        elif state=="quote":
            if ch=="\\":i+=1
            elif ch=='"':state="code"
        elif state=="char":
            if ch=="\\":i+=1
            elif ch=="'":state="code"
        else:
            if ch=="/" and nxt=="/":
                state="line";i+=1
            elif ch=="/" and nxt=="*":
                state="block";i+=1
            elif ch=='"':state="quote"
            elif ch=="'":state="char"
            elif ch=="{":depth+=1
            elif ch=="}":
                depth-=1
                if depth==0:
                    return raw[:i+1]
                if depth<0:
                    raise ValueError("V255 unmatched native C++ closing brace")
        i+=1
    raise ValueError("V255 unterminated generated C++ function")

def compare(before:str,after:str)->str:
    old=functions(before);new=functions(after)
    if not old or not new or not TARGETS.issubset(old) or not TARGETS.issubset(new):
        raise ValueError("V255 missing original restored callback entries")
    if not all(old[k]!=new[k] for k in TARGETS):
        raise ValueError("V255 restored callbacks unexpectedly identical")
    if not all(k in old and k in new and old[k]==new[k] for k in CONTROLS.values()):
        raise ValueError("V255 native runtime control function changed")
    changed=sorted(k for k in (set(old)&set(new))-TARGETS if old[k]!=new[k])
    if len(changed)!=1:
        raise ValueError("V255 extra changed-function count differs from V253")
    pc=changed[0]
    last=pc==next(reversed(old)) and pc==next(reversed(new))
    if not last:
        raise ValueError("V255 extra changed function is not terminal")
    a=body_only(old[pc]);b=body_only(new[pc])
    same=a==b
    tail_diff=old[pc][len(a):]!=new[pc][len(b):]
    return ("V255_AOT_TAIL parsed=1 last=1 pc="+f"{pc:08x}"+
            " body_same="+str(int(same))+
            " tail_diff="+str(int(tail_diff))+
            " controls=1 extras=1")

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_baseline_cpp",type=Path)
    p.add_argument("private_restored_cpp",type=Path)
    a=p.parse_args()
    try:
        old=a.private_baseline_cpp.read_text(encoding="utf-8",errors="replace")
        new=a.private_restored_cpp.read_text(encoding="utf-8",errors="replace")
        result=compare(old,new)
    except (OSError,ValueError,IndexError):
        print("V255_AOT_TAIL_DIAG reason=unavailable")
        return 1
    print(result)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
