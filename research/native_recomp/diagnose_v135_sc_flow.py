#!/usr/bin/env python3
"""V135 classify original Wii SC helper callgraph and status critical section.

Outputs source addresses, branch classes and register identifiers, never bytes.
"""
import argparse,hashlib,struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,BLR,target,text_at
from diagnose_v132_sc_status import ENTRY,SIZE,RD_MAJOR
from audit_sc_status_writer_sites import STATUS_OFFSET

STATUS_LOAD=0x8052F84C
STATUS_CLEAR=0x8052F85C
STATUS_RESTORE=0x8052F920

def decode(body:bytes)->dict:
    if len(body)!=SIZE:
        raise ValueError("V135 original SC helper size mismatch")
    w=struct.unpack(">"+"I"*(SIZE//4),body)
    if w[0]>>26!=37 or w[-1]!=BLR:
        raise ValueError("V135 original SC helper bounds differ")
    def at(pc):return w[(pc-ENTRY)//4]
    ld=at(STATUS_LOAD);zero=at(STATUS_CLEAR);restore=at(STATUS_RESTORE)
    if ((ld>>26),(ld>>21)&31,(ld>>16)&31,(ld&65535))!=(34,29,13,STATUS_OFFSET&65535):
        raise ValueError("V135 original SC SDA load differs")
    for word,reg in ((zero,0),(restore,29)):
        if (word>>26,(word>>21)&31,(word>>16)&31,word&65535)!=(38,reg,13,STATUS_OFFSET&65535):
            raise ValueError("V135 status-byte critical-section write differs")
    calls=[];conditional=[];r3=[];comparisons=[]
    for i,word in enumerate(w):
        pc=ENTRY+4*i
        major=word>>26
        if major==18 and word&3==1:
            calls.append((pc,target(word,pc,True)))
        if major==16:
            disp=word&0xfffc
            if disp&0x8000:disp-=0x10000
            dest=(disp if word&2 else pc+disp)&0xffffffff
            conditional.append((pc,dest,(word>>21)&31,(word>>16)&31))
        if major in RD_MAJOR and (word>>21)&31==3:
            r3.append((pc,major))
        if major in (10,11):
            comparisons.append((pc,(word>>16)&31,word&0xffff))
    if len(calls)!=12 or len(r3)!=2:
        raise ValueError("V135 original caller/dataflow counts differ")
    return {"calls":calls,"branches":conditional,"r3":r3,"compares":comparisons,
            "loadreg":(ld>>21)&31,
            "clearreg":(zero>>21)&31,
            "restorereg":(restore>>21)&31}

def report(d:dict)->list[str]:
    out=[f"V135_SC_GRAPH calls={len(d['calls'])} branches={len(d['branches'])} r3writes={len(d['r3'])} comparisons={len(d['compares'])} loadreg={d['loadreg']} clearreg={d['clearreg']} restorereg={d['restorereg']}"]
    for pc,dest in d["calls"][:16]:
        out.append(f"V135_SC_CALL pc={pc:08x} dest={dest:08x}")
    for pc,major in d["r3"][:8]:
        out.append(f"V135_SC_R3WRITE pc={pc:08x} major={major}")
    for pc,dest,bo,bi in d["branches"][:16]:
        out.append(f"V135_SC_BRANCH pc={pc:08x} dest={dest:08x} bo={bo} bi={bi}")
    for pc,reg,imm in d["compares"][:8]:
        out.append(f"V135_SC_COMPARE pc={pc:08x} reg={reg} imm={imm}")
    return out

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sha_authenticated_original",type=Path)
    args=ap.parse_args()
    try:
        raw=args.sha_authenticated_original.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
            raise ValueError("V135 original SHA differs")
        graph=decode(text_at(raw,ENTRY,SIZE))
    except Exception:
        print("V135_SC_GRAPH result=failed")
        return 1
    for line in report(graph):print(line)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
