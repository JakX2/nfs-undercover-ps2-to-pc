#!/usr/bin/env python3
"""V51 private original-Wii continuous __start -> second __OSCacheInit call.

__OSCacheInit's authentic owner PowerPC was already installed at 0x80522540
and executed by __start in V20; do not duplicate or overwrite it. Connect
the SHA-authenticated OSInit call at 0x805208C0 and bound the next OSInit
service with a conspicuous test-only sc;blr at 0x805208C4.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_context_v50 import make as make_v50,STOP as OLD_STOP
from make_start_to_irq_return_v49 import START
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_cache_slice_v20 import CACHE_BYTES

CACHE=0x80522540
STOP=0x805208C4

def make(owner:Path)->bytes:
    previous=make_v50(owner)
    raw=owner.read_bytes()
    original_call=text_at(raw,OLD_STOP,4)
    if call_target(original_call,OLD_STOP,OLD_STOP)!=CACHE:
        raise ValueError("original OSInit second cache initialization BL target changed")
    at=locate(previous,OLD_STOP,12)
    if previous[at:at+12]!=struct.pack(">III",SC,BLR,NOP):
        raise ValueError("V50 native OSInit cache checkpoint modified")
    cached_at=locate(previous,CACHE,CACHE_BYTES)
    original_cache=text_at(raw,CACHE,CACHE_BYTES)
    if previous[cached_at:cached_at+CACHE_BYTES]!=original_cache:
        raise ValueError("original __OSCacheInit from __start no longer SHA-identical")
    if word(original_cache,CACHE_BYTES-4)!=BLR:
        raise ValueError("original cache initializer return instruction changed")
    result=bytearray(previous)
    result[at:at+4]=original_call
    result[at+4:at+12]=struct.pack(">II",SC,BLR)
    if result[:256]!=previous[:256] or word(result,0xe0)!=START:
        raise ValueError("V51 original executable metadata/entry changed")
    return bytes(result)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    args=p.parse_args()
    if args.private_fixture.exists() or args.private_fixture.is_symlink():
        p.error("refusing to overwrite owner-private fixture")
    args.private_fixture.write_bytes(make(args.owner_original_dol))
    print("PASS: genuine original Wii V51 second cache initialization fixture")
