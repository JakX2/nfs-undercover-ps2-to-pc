#!/usr/bin/env python3
"""V127 owner-private authenticated OSInit continuation, exactly four PPC words."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,SC,BLR,NOP,text_at
from make_start_to_irq_enable_v68 import replace

ENTRY=0x8052096C
SIZE=0x10
OLD=struct.pack(">IIII",SC,BLR,NOP,NOP)
NEXT_STUB=struct.pack(">II",SC,BLR)

def body_from_owner(owner:bytes)->bytes:
    if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("V127 original Wii authentication failed")
    body=text_at(owner,ENTRY,SIZE)
    words=struct.unpack(">IIII",body)
    majors=tuple(w>>26 for w in words)
    link_mask=sum((1<<i) for i,w in enumerate(words)
                  if (w>>26) in (16,18,19) and (w&1))
    if majors!=(18,10,16,18) or link_mask!=9:
        raise ValueError("V127 original OSInit instruction structure differs")
    if body==OLD:
        raise ValueError("V127 authentic continuation still synthetic")
    return body

def restore(fixture:bytes,body:bytes)->bytes:
    if len(body)!=SIZE:
        raise ValueError("V127 original continuation span differs")
    earlier=text_at(fixture,ENTRY,SIZE)
    if earlier!=OLD or text_at(fixture,ENTRY+SIZE,8)!=NEXT_STUB:
        raise ValueError("V127 inherited OSInit synthetic boundaries differ")
    result=bytearray(fixture)
    replace(result,ENTRY,OLD,body)
    reverse=bytearray(result)
    replace(reverse,ENTRY,body,OLD)
    if bytes(reverse)!=fixture or result[:256]!=fixture[:256] or len(result)!=len(fixture):
        raise ValueError("V127 fixture modified outside authenticated OSInit window")
    return bytes(result)

def make(fixture:Path,owner:Path)->bytes:
    authenticated=body_from_owner(owner.read_bytes())
    return restore(fixture.read_bytes(),authenticated)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("canonical_private_fixture",type=Path)
    p.add_argument("authenticated_owner",type=Path)
    p.add_argument("output_private_fixture",type=Path)
    a=p.parse_args()
    if a.output_private_fixture.exists() or a.output_private_fixture.is_symlink():
        p.error("refusing private overwrite")
    try:
        private=make(a.canonical_private_fixture,a.authenticated_owner)
        with a.output_private_fixture.open("xb") as out:
            out.write(private)
    except Exception:
        print("V127_OSINIT_RESTORE ok=0")
        return 1
    print("V127_OSINIT_RESTORE ok=1")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
