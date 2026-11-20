#!/usr/bin/env python3
"""V128 original Wii post-OSInit function extent and synthetic-stub audit.

No original instruction bytes or decompiled code are published. Every original
instruction comes only from the SHA-pinned private owner DOL.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from extend_private_text import STUB,NOP,unpack
from make_osinit_execparams_v28 import ORIGINAL_SHA,BLR,target,text_at

ENTRY=0x8052F830
NEXT_KNOWN=0x8052F94C
MAX_SPAN=NEXT_KNOWN-ENTRY
CALLSITE=0x8052096C

def probe(owner:bytes,fixture:bytes)->dict[str,int]:
    original=text_at(owner,ENTRY,MAX_SPAN)
    slots=unpack(fixture)
    found=[(base,payload) for kind,index,base,payload in slots
           if kind==0 and base<=ENTRY and ENTRY+8<=base+len(payload)]
    if len(found)!=1:
        return {"mapped":0,"prefix":0,"capacity":0,
                "returns":0,"first_end":0,"last_end":0,
                "eligible_first":0,"eligible_last":0,
                "major0":int.from_bytes(original[:4],'big')>>26}
    base,data=found[0]
    pos=ENTRY-base
    prefix=bytes(data[pos:pos+8])
    auth=original[:8]
    kind=1 if prefix==STUB else 2 if prefix==NOP*2 else 3 if prefix==auth else 4
    limit=min(MAX_SPAN,len(data)-pos)
    n=8
    if kind in (1,2):
        while n+4<=limit and bytes(data[pos+n:pos+n+4])==NOP:
            n+=4
    else:
        n=0
    returns=[i+4 for i in range(0,len(original),4)
             if original[i:i+4]==struct.pack(">I",BLR)]
    first=returns[0] if returns else 0
    last=returns[-1] if returns else 0
    return {"mapped":1,"prefix":kind,"capacity":n//4,
            "returns":len(returns),"first_end":first//4,"last_end":last//4,
            "eligible_first":int(bool(first) and first<=n),
            "eligible_last":int(bool(last) and last<=n),
            "major0":int.from_bytes(original[:4],'big')>>26}

def report(x:dict[str,int])->str:
    fields=("mapped","prefix","capacity","returns","first_end","last_end",
            "eligible_first","eligible_last","major0")
    return "V128_NEXT_PROBE "+" ".join(f"{k}={x[k]}" for k in fields)

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("authenticated_owner",type=Path)
    ap.add_argument("v127_private_fixture",type=Path)
    args=ap.parse_args()
    try:
        raw=args.authenticated_owner.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
            raise ValueError("V128 SHA-pinned original Wii DOL mismatch")
        word=struct.unpack(">I",text_at(raw,CALLSITE,4))[0]
        if target(word,CALLSITE,True)!=ENTRY:
            raise ValueError("V128 original call edge differs")
        result=probe(raw,args.v127_private_fixture.read_bytes())
        if not result["mapped"]:
            raise ValueError("V128 original function lacks mapped guest text")
    except Exception:
        print("V128_NEXT_PROBE result=failed")
        return 1
    print(report(result))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
