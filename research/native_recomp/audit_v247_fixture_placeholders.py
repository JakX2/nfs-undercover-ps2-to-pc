#!/usr/bin/env python3
"""V247 private callback/NAND fixture-word census; print counts only.

A SHA-256-authenticated owner DOL and ephemeral AOT fixture are read in
owner CI. Differing words are classified as original-free NOP, syscall,
return, zero or other. Never print original game bytes, paths or pointers.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA, text_at
from audit_v245_generated_callback import SPANS

KINDS=("same","nop","sc","blr","zero","other")

def summarize(original:bytes,fixture:bytes)->dict[str,int]:
    if not original or len(original)!=len(fixture) or len(original)%4:
        raise ValueError("V247 fixture word geometry differs")
    result=dict.fromkeys(KINDS,0)
    for off in range(0,len(original),4):
        old=struct.unpack_from(">I",original,off)[0]
        new=struct.unpack_from(">I",fixture,off)[0]
        name=("same" if old==new else "nop" if new==0x60000000
              else "sc" if new==0x44000002 else "blr" if new==0x4e800020
              else "zero" if new==0 else "other")
        result[name]+=1
    return result

def inspect(original:bytes,fixture:bytes)->dict[str,dict[str,int]]:
    if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("V247 private owner authentication differs")
    counts={k:summarize(text_at(original,addr,n),text_at(fixture,addr,n))
            for k,(addr,n) in SPANS.items()}
    for key in ("isfs","ipc"):
        if counts[key]["same"]!=SPANS[key][1]//4:
            raise ValueError("V247 authenticated control function differs")
    return counts

def render(counts:dict[str,dict[str,int]])->str:
    chunks=["V247_FIXTURE","owner=1"]
    for part in ("cb","nand"):
        for name in KINDS:
            chunks.append(f"{part}_{name}={counts[part][name]}")
        chunks.append(f"{part}_placeholder={int(counts[part]['other']==0 and counts[part]['zero']==0)}")
    return " ".join(chunks)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("original",type=Path);p.add_argument("fixture",type=Path)
    a=p.parse_args()
    try:
        result=inspect(a.original.read_bytes(),a.fixture.read_bytes())
    except (OSError,ValueError):
        print("V247_FIXTURE_DIAG result=failed")
        raise SystemExit(1)
    print(render(result))
