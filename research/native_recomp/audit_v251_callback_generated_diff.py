#!/usr/bin/env python3
"""V251 owner-local generated AOT function-body differential audit.

Compare only the privately emitted translated C++ from the reduced Wii
startup fixture and SHA-restored callback fixture. Public output consists
exclusively of aggregate counts and control-function boolean equality.
Never print, export or commit original PPC bytes or generated C++ bodies.
"""
import argparse
import re
from pathlib import Path
from audit_v245_generated_callback import HEADERS, CALLS

TRACE=re.compile(r"nwii::runtime::trace_call\(0x([0-9a-fA-F]{8}), ctx\)")
TARGETS={CALLS["cb"],CALLS["nand"]}
CONTROLS={"isfs":CALLS["isfs"],"ipc":0x805190c0,"async":0x8051982c}

def functions(text:str)->dict[int,str]:
    anchors=list(HEADERS.finditer(text))
    result={}
    for index,anchor in enumerate(anchors):
        end=anchors[index+1].start() if index+1<len(anchors) else len(text)
        body=text[anchor.start():end]
        found=TRACE.findall(body)
        if len(found)!=1:
            continue
        address=int(found[0],16)
        if address in result:
            raise ValueError("V251 duplicate translated trace entry")
        result[address]=body
    return result

def compare(before:str,after:str)->str:
    b=functions(before);a=functions(after)
    if not b or not a or not TARGETS.issubset(b) or not TARGETS.issubset(a):
        raise ValueError("V251 missing expected generated callback entry")
    shared=set(b)&set(a)
    elsewhere=shared-TARGETS
    updated=sum(b[k]!=a[k] for k in elsewhere)
    new=len((set(a)-set(b))-TARGETS)
    lost=len((set(b)-set(a))-TARGETS)
    controls={k:int(pc in b and pc in a and b[pc]==a[pc])
              for k,pc in CONTROLS.items()}
    return ("V251_AOT_DIFF parsed=1 cb="+str(int(b[CALLS["cb"]]!=a[CALLS["cb"]]))+
            " nand="+str(int(b[CALLS["nand"]]!=a[CALLS["nand"]]))+
            " ipc="+str(controls["ipc"])+
            " isfs="+str(controls["isfs"])+
            " async="+str(controls["async"])+
            " changed="+str(min(updated,999999))+
            " new="+str(min(new,999999))+
            " removed="+str(min(lost,999999)))

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_baseline_aot",type=Path)
    p.add_argument("private_restored_aot",type=Path)
    args=p.parse_args()
    try:
        before=args.private_baseline_aot.read_text(encoding="utf-8",errors="replace")
        after=args.private_restored_aot.read_text(encoding="utf-8",errors="replace")
        result=compare(before,after)
    except (OSError,ValueError):
        print("V251_AOT_DIFF_DIAG reason=unavailable")
        return 1
    print(result)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
