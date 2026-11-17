#!/usr/bin/env python3
"""V54 owner-original exact-range and no-overwrite DOL geometry oracle."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_eximask_v53 import make as make_v53
from make_start_to_exi_handlers_v54 import (
    HANDLER,HANDLER_SIZE,EXI,OLD_STOP,STOP,START,verify_original,
)
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word

def verify(actual:bytes,owner:Path)->None:
    prev=make_v53(owner)
    handler,exi=verify_original(owner.read_bytes())
    before,before_data=sections_of(prev)
    after,after_data=sections_of(actual)
    if (len(before)!=7 or len(after)!=7 or after_data!=before_data or
        word(actual,0xE0)!=START or actual[0xE0:0x100]!=prev[0xE0:0x100]):
        raise ValueError("V54 changed Wii entrypoint or non-code DOL sections")
    hits=0
    for i,((base,orig),(new_base,now)) in enumerate(zip(before,after)):
        if base!=new_base:
            raise ValueError("V54 shifted an existing guest text section")
        expected=bytearray(orig)
        if base<=HANDLER and HANDLER+HANDLER_SIZE<=base+len(orig):
            hits+=1
            at=HANDLER-base
            if expected[at:at+HANDLER_SIZE]!=struct.pack(">I",NOP)*(HANDLER_SIZE//4):
                raise ValueError("V53 EXI handler setter destination was not synthetic NOP")
            expected[at:at+HANDLER_SIZE]=handler
        if i==6:
            if expected[EXI-base:OLD_STOP-base]!=exi[:OLD_STOP-EXI]:
                raise ValueError("V54 altered the previously verified original EXI prefix")
            if expected[OLD_STOP-base:]!=struct.pack(">II",SC,BLR):
                raise ValueError("V53 synthetic EXI stop does not match")
            expected[OLD_STOP-base:]=exi[OLD_STOP-EXI:]+struct.pack(">II",SC,BLR)
            if len(expected)!=STOP+8-base:
                raise ValueError("V54 EXI section length differs")
        if now!=expected:
            raise ValueError("V54 modified earlier verified original PowerPC bytes")
    if hits!=1:
        raise ValueError("V54 handler replacement did not map exactly one segment")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_dol)
    print("PASS: V54 exact original EXI setter and handler table no-overwrite geometry")
