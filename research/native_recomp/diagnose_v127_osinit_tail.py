#!/usr/bin/env python3
"""V127 read-only authenticated OSInit continuation audit, no original code output."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,SC,BLR,NOP,text_at

START=0x8052096C
SIZE=0x10
SYNTHETIC=(SC,BLR,NOP,NOP)

def words(image:bytes)->tuple[int,int,int,int]:
    return struct.unpack(">IIII",text_at(image,START,SIZE))

def classify(original:tuple[int,...],fixture:tuple[int,...])->dict[str,int]:
    if len(original)!=4 or len(fixture)!=4:
        raise ValueError("V127 bounded window must contain exactly four words")
    major=lambda word:word>>26
    return {
      "placeholder":int(tuple(fixture)==SYNTHETIC),
      "changed":int(tuple(original)!=SYNTHETIC),
      "first_branch":int(major(original[0]) in (16,18,19)),
      "first_syscall":int(major(original[0])==17),
      "branch_count":sum(major(w) in (16,18,19) for w in original),
      "return_count":sum(w==BLR for w in original),
      "nop_count":sum(w==NOP for w in original),
      "syscall_count":sum(major(w)==17 for w in original),
      "major0":major(original[0]),
      "major1":major(original[1]),
      "major2":major(original[2]),
      "major3":major(original[3]),
      "link_mask":sum((1<<i) for i,w in enumerate(original)
                      if major(w) in (16,18,19) and (w&1)),
      "direct_mask":sum((1<<i) for i,w in enumerate(original)
                        if major(w)==18),

    }
def report(data:dict[str,int])->str:
    fields=("placeholder","changed","first_branch","first_syscall",
            "branch_count","return_count","nop_count","syscall_count",
            "major0","major1","major2","major3","link_mask","direct_mask")
    return "V127_OSINIT_WINDOW "+" ".join(f"{k}={data[k]}" for k in fields)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("authenticated_owner",type=Path)
    p.add_argument("canonical_private_fixture",type=Path)
    args=p.parse_args()
    try:
        original=args.authenticated_owner.read_bytes()
        if hashlib.sha256(original).hexdigest()!=ORIGINAL_SHA:
            raise ValueError("V127 authentication failed")
        result=classify(words(original),words(args.canonical_private_fixture.read_bytes()))
        if result["placeholder"]!=1 or result["changed"]!=1:
            raise ValueError("V127 canonical fixture does not preserve the expected boundary")
    except Exception:
        print("V127_OSINIT_WINDOW result=failed")
        return 1
    print(report(result))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
