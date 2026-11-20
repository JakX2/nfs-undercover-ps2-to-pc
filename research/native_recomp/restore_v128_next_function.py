#!/usr/bin/env python3
"""V128 restore exactly 71 SHA-authenticated original Wii instructions privately."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,BLR,NOP,target,text_at
from make_start_to_irq_enable_v68 import replace

ENTRY=0x8052F830
END=0x8052F94C
SIZE=END-ENTRY
CALLSITE=0x8052096C
EMPTY=struct.pack(">I",NOP)*(SIZE//4)

def owner_body(owner:bytes)->bytes:
    if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("V128 authenticated original Wii owner differs")
    instruction=struct.unpack(">I",text_at(owner,CALLSITE,4))[0]
    if target(instruction,CALLSITE,True)!=ENTRY:
        raise ValueError("V128 authenticated OSInit BL target differs")
    body=text_at(owner,ENTRY,SIZE)
    verify_body(body)
    return body

def verify_body(body:bytes)->None:
    if len(body)!=SIZE:
        raise ValueError("V128 restored body extent differs")
    words=struct.unpack(">"+("I"*(SIZE//4)),body)
    if (words[0]>>26)!=37 or words[-1]!=BLR or words.count(BLR)!=1:
        raise ValueError("V128 original function boundary differs")

def restore(fixture:bytes,body:bytes)->bytes:
    verify_body(body)
    before=text_at(fixture,ENTRY,SIZE)
    if before!=EMPTY:
        raise ValueError("V128 original code placeholder is not an exact NOP span")
    next_old=text_at(fixture,END,4)
    result=bytearray(fixture)
    replace(result,ENTRY,EMPTY,body)
    if bytes(result[:256])!=fixture[:256] or len(result)!=len(fixture):
        raise ValueError("V128 DOL header or private layout changed")
    if text_at(result,END,4)!=next_old:
        raise ValueError("V128 next function boundary mutated")
    reversed_image=bytearray(result)
    replace(reversed_image,ENTRY,body,EMPTY)
    if bytes(reversed_image)!=fixture:
        raise ValueError("V128 mutation extends beyond authenticated function")
    return bytes(result)

def make(fixture:Path,owner:Path)->bytes:
    return restore(fixture.read_bytes(),owner_body(owner.read_bytes()))

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("inherited_v127_fixture",type=Path)
    ap.add_argument("sha_authenticated_owner",type=Path)
    ap.add_argument("new_private_fixture",type=Path)
    args=ap.parse_args()
    if args.new_private_fixture.exists() or args.new_private_fixture.is_symlink():
        ap.error("refusing private DOL overwrite")
    try:
        result=make(args.inherited_v127_fixture,args.sha_authenticated_owner)
        with args.new_private_fixture.open("xb") as out:out.write(result)
    except Exception:
        print("V128_ORIGINAL_RESTORE ok=0")
        return 1
    print("V128_ORIGINAL_RESTORE ok=1")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
