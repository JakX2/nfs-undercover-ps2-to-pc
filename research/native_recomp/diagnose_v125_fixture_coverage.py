#!/usr/bin/env python3
"""SHA-pinned owner-original/fixture code coverage audit, boolean-only public output."""
import argparse
import hashlib
import struct
from pathlib import Path
from make_osinit_execparams_v28 import ORIGINAL_SHA,NOP,text_at

PC=0x8051E5BC

def decode_words(blob):
    try:
        a=text_at(blob,PC,8)
        return struct.unpack(">II",a)
    except ValueError:
        return None

def inspect(fixture:bytes,original:bytes):
    test=decode_words(fixture)
    owner=decode_words(original)
    return dict(mapped=int(test is not None),
                owner=int(owner is not None),
                zero=int(test is not None and test[0]==0 and test[1]==0),
                nop=int(test is not None and test[0]==NOP and test[1]==NOP),
                same=int(test is not None and owner is not None and test==owner))

def render(info):
    return "V125_FIXTURE_CODE "+" ".join(f"{k}={info[k]}" for k in ("mapped","owner","zero","nop","same"))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("authenticated_owner",type=Path)
    a=p.parse_args()
    owner=a.authenticated_owner.read_bytes()
    if hashlib.sha256(owner).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("private owner SHA-256 validation failed")
    print(render(inspect(a.private_fixture.read_bytes(),owner)))

if __name__=="__main__":
    main()
