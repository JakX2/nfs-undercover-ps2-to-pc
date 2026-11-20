#!/usr/bin/env python3
"""V132 privately classify Wii original SC status helper control/data flow.

Original executable and any translated instructions remain private.
Outputs include bounded instruction categories and addresses only.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,BLR,target,text_at

ENTRY=0x8052F830
SIZE=0x11C
DISABLE_AT=0x8052F848
RESTORE_AT=0x8052F928
DISABLE_DEST=0x805265AC
RESTORE_DEST=0x805265D4
MEMORY_LOADS=frozenset((32,33,34,35,40,41,42,43,46,47,48,49,50,51))
MEMORY_STORES=frozenset((36,37,38,39,44,45,52,53,54,55))
RD_MAJOR=frozenset((14,15,24,25,26,27,28,29,32,33,34,35,40,41,42,43,46,47,48,49,50,51))

def inspect(body:bytes)->dict[str,object]:
    if len(body)!=SIZE:
        raise ValueError("V132 original SC function size differs")
    words=struct.unpack(">"+("I"*(SIZE//4)),body)
    if words[0]>>26!=37 or words[-1]!=BLR or words.count(BLR)!=1:
        raise ValueError("V132 original SC function geometry differs")
    li1,li0,lim1=[],[],[]
    r3write,loads,stores,sda,edges=[],[],[],[],[]
    for i,w in enumerate(words):
        pc=ENTRY+4*i
        op=w>>26
        rd=(w>>21)&31
        ra=(w>>16)&31
        imm=w&0xFFFF
        if op==14 and rd==3 and ra==0:
            if imm==1:li1.append(pc)
            if imm==0:li0.append(pc)
            if imm==0xFFFF:lim1.append(pc)
        if rd==3 and op in RD_MAJOR:r3write.append(pc)
        if op in MEMORY_LOADS:loads.append(pc)
        if op in MEMORY_STORES:stores.append(pc)
        if op in MEMORY_LOADS and ra in (2,13):
            sda.append((pc,op,ra,imm if imm<0x8000 else imm-0x10000))
        if op==18 and (w&3)==1:
            edges.append((pc,target(w,pc,True)))
    def direct_edge(at,dest):
        return int((at,dest) in edges)
    return {"disable":direct_edge(DISABLE_AT,DISABLE_DEST),
            "restore":direct_edge(RESTORE_AT,RESTORE_DEST),
            "calls":len(edges),"loads":len(loads),"stores":len(stores),
            "sda_reads":len(sda),"r3writes":len(r3write),
            "li1":len(li1),"li0":len(li0),"lim1":len(lim1),
            "li1_sites":li1,"li0_sites":li0,"lim1_sites":lim1,
            "sda_sites":sda,"r3write_sites":r3write}

def report(data:dict[str,object])->str:
    keys=("disable","restore","calls","loads","stores","sda_reads",
          "r3writes","li1","li0","lim1")
    main="V132_SC_STATUS "+" ".join(f"{key}={data[key]}" for key in keys)
    return main

def format_site_list(data:dict[str,object])->list[str]:
    # Only metadata, no opcode or instruction bytes. Limit to eight entries.
    result=[]
    for name in ("li1_sites","li0_sites","lim1_sites"):
        pcs=data[name]
        if not isinstance(pcs,list):raise ValueError("unexpected status site type")
        for pc in pcs[:8]:
            result.append(f"V132_STATUS_ASSIGN kind={name} pc={pc:08x}")
    for pc,op,base,off in data["sda_sites"][:8]:
        result.append(f"V132_STATUS_SDA pc={pc:08x} major={op} base={base} offset={off}")
    return result

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sha_authenticated_wii_owner",type=Path)
    args=ap.parse_args()
    try:
        raw=args.sha_authenticated_wii_owner.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
            raise ValueError("V132 original Wii DOL SHA differs")
        data=inspect(text_at(raw,ENTRY,SIZE))
        if data["disable"]!=1 or data["restore"]!=1:
            raise ValueError("V132 original critical-section edges differ")
    except Exception:
        print("V132_SC_STATUS result=failed")
        return 1
    print(report(data))
    for line in format_site_list(data):print(line)
    return 0
if __name__=="__main__":
    raise SystemExit(main())
