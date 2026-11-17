#!/usr/bin/env python3
"""Owner-private V38 authentic Wii exception-vector memcpy continuation.

The original handler and PPC instructions are read only from the exact
SHA-pinned owner DOL; any generated game C++ remains in private runner scratch.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import struct

from make_start_to_vectorclear_v37 import make as make_v37, OSINIT, STOP as PREVIOUS_STOP, word
from make_osinit_vectorcopy_v42 import (
    COPY_START, COPY_CALL, CACHE_STOP, CACHE_FUNC, MEMCPY,
    TEMPLATE_SRC, TEMPLATE_SIZE, PRIVATE_DATA_GUEST
)
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text, linked_target
from make_start_to_data_v23 import SC, BLR

STOP=CACHE_STOP


def make(owner:Path)->bytes:
    raw=owner.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=ORIGINAL_SHA:
        raise ValueError("incorrect owner Wii original executable SHA256")
    prior=bytearray(make_v37(owner))
    if PREVIOUS_STOP!=COPY_START:
        raise ValueError("V37 boundary no longer matches original exception copy")
    section_off,section_guest,section_size=(word(prior,k+4) for k in (0,0x48,0x90))
    at=section_off+COPY_START-section_guest
    if section_off<256 or section_guest!=OSINIT or at<section_off or at+44>section_off+section_size:
        raise ValueError("original exception text not in expected section")
    if prior[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V37 bounded stop before vector memcpy missing")
    code=get_text(raw,COPY_START,CACHE_STOP-COPY_START)
    template=get_text(raw,TEMPLATE_SRC,TEMPLATE_SIZE)
    if len(code)!=36 or len(template)!=0x98:
        raise ValueError("original Wii handler template or memcpy instructions truncated")
    if linked_target(word(code,COPY_CALL-COPY_START),COPY_CALL)!=MEMCPY:
        raise ValueError("original exception vector memcpy call target changed")
    cache_bl=get_text(raw,CACHE_STOP,4)
    if linked_target(word(cache_bl,0),CACHE_STOP)!=CACHE_FUNC:
        raise ValueError("unexpected original cache-flush service call target")
    prior[at:at+len(code)]=code
    struct.pack_into(">II",prior,section_off+STOP-section_guest,SC,BLR)

    # The original startup fixture already carries its unmodified __init_data
    # relocator table in the FIRST DOL data section. Preserve it and add only
    # one independent, non-executable private-oracle segment for the 0x98-byte
    # handler template. NWiiRuntime test seeds guest source memory from it.
    if word(prior,0x64)!=0x80006420 or word(prior,0xac)!=0xB0:
        raise ValueError("original Wii startup data table missing")
    if any(word(prior,k) for k in (0x20,0x68,0xb0)):
        raise ValueError("private fixture second data segment already allocated")
    data_off=(len(prior)+3)&~3
    prior.extend(b"\0"*(data_off-len(prior)))
    prior.extend(template)
    for k,v in ((0x20,data_off),(0x68,PRIVATE_DATA_GUEST),(0xb0,TEMPLATE_SIZE)):
        struct.pack_into(">I",prior,k,v)
    return bytes(prior)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_test_dol",type=Path)
    a=p.parse_args()
    if a.private_test_dol.exists() or a.private_test_dol.is_symlink():
        p.error("refusing overwrite of owner-derived private image")
    a.private_test_dol.write_bytes(make(a.owner_original_dol))
    print("PASS: original Wii V38 continuous private vector-memcpy test DOL constructed")
