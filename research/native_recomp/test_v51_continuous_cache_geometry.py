#!/usr/bin/env python3
"""V51 original Wii cache-call and exact no-overwrite geometry oracle."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_context_v50 import make as make_v50,STOP as OLD_STOP
from make_start_to_cache_reuse_v51 import STOP,CACHE,START,CACHE_BYTES
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR

def verify(actual:bytes,owner:Path)->None:
    old=make_v50(owner)
    if len(actual)!=len(old) or actual[:256]!=old[:256] or word(actual,0xe0)!=START:
        raise ValueError("V51 owner Wii DOL size/header/section mapping changed")
    offset=locate(actual,OLD_STOP,12)
    allowed=set(range(offset,offset+12))
    for i,(a,b) in enumerate(zip(old,actual)):
        if i not in allowed and a!=b:
            raise ValueError("V51 original startup or helper instruction overwritten")
    if actual[offset:offset+4]!=text_at(owner.read_bytes(),OLD_STOP,4):
        raise ValueError("V51 original OSInit->__OSCacheInit branch changed")
    if actual[offset+4:offset+12]!=struct.pack(">II",SC,BLR):
        raise ValueError("V51 next OSInit service lacks test-only stop")
    pc=locate(actual,CACHE,CACHE_BYTES)
    if actual[pc:pc+CACHE_BYTES]!=text_at(owner.read_bytes(),CACHE,CACHE_BYTES):
        raise ValueError("V51 reused original Wii cache initializer differs")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    args=p.parse_args()
    verify(args.private_fixture.read_bytes(),args.owner_original_dol)
    print("PASS: V51 source-backed second __OSCacheInit BL and no-overwrite guards")
