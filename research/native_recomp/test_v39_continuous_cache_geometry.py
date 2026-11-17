#!/usr/bin/env python3
"""V39 fail-closed owner-original cache-loop verification and no-overwrite guard."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct
from make_start_to_vectorcopy_v38 import make as make_v38,OSINIT,word
from make_start_to_cache_v39 import STOP
from make_osinit_cache_v43 import FIRST_CACHE,FIRST_CACHE_LEN,SECOND_CACHE,SECOND_CACHE_LEN
from make_osinit_execparams_v28 import text_at,SC,BLR
from make_hardware_boundary_v17 import ORIGINAL_SHA

def verify(image:bytes,owner:Path)->None:
    source=owner.read_bytes()
    if hashlib.sha256(source).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("original-owner Wii DOL digest differs")
    before=make_v38(owner)
    if len(image)!=len(before) or image[:256]!=before[:256] or word(image,0xE0)!=0x8000403C:
        raise ValueError("V39 original __start/private DOL geometry changed")
    off,guest,count=(word(image,k) for k in (0,0x48,0x90))
    if off<256 or guest!=OSINIT or STOP+8>guest+count:
        raise ValueError("original Wii cache region outside bounded test image")
    intervals=((0x80520DA4,STOP+8),(FIRST_CACHE,FIRST_CACHE+FIRST_CACHE_LEN),
               (SECOND_CACHE,SECOND_CACHE+SECOND_CACHE_LEN))
    allowed=set()
    for first,last in intervals:
        if first<guest or last>guest+count:
            raise ValueError("unmapped V39 original Wii cache code")
        allowed.update(range(off+first-guest,off+last-guest))
    for pos,(old,new) in enumerate(zip(before,image)):
        if pos not in allowed and old!=new:
            raise ValueError("V39 changed bytes outside authenticated cache continuation")
    for first,last in ((0x80520DA4,STOP),(FIRST_CACHE,FIRST_CACHE+FIRST_CACHE_LEN),
                       (SECOND_CACHE,SECOND_CACHE+SECOND_CACHE_LEN)):
        at=off+first-guest
        if image[at:at+last-first]!=text_at(source,first,last-first):
            raise ValueError("original PPC cache helper instructions differ")
    if image[off+STOP-guest:off+STOP-guest+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V39 guest-PC test-only stop is missing")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: V39 original cache helper byte-for-byte guards and geometry verified")
