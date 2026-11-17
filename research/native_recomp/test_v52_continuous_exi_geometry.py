#!/usr/bin/env python3
"""Private V52 no-overwrite oracle for seven-slot continuous EXI expansion."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path

from make_start_to_cache_reuse_v51 import make as make_v51
from make_start_to_exi_poll_v52 import (
    START, OSINIT_CALL, OSINIT_GUARD, EXI, STOP, DBINIT, DEBUG, EXI_LENGTH, verify_prefix,
)
from make_start_to_epilogue_v41 import sections_of
from make_start_to_module_v44 import locate
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_start_to_vectorcopy_v38 import word

def verify(actual:bytes,owner:Path)->None:
    old=make_v51(owner)
    old_text,old_data=sections_of(old)
    new_text,new_data=sections_of(actual)
    if word(actual,0xE0)!=START or actual[0xE0:0x100]!=old[0xE0:0x100]:
        raise ValueError("V52 guest entry or header metadata changed")
    if len(old_text)!=7 or len(new_text)!=7 or new_data!=old_data:
        raise ValueError("V52 text/data sections changed unexpectedly")
    original_call=text_at(owner.read_bytes(),OSINIT_CALL,4)
    original_exi=text_at(owner.read_bytes(),EXI,EXI_LENGTH)
    verify_prefix(original_exi)
    for index in range(6):
        guest,code=new_text[index]
        old_guest,old_code=old_text[index]
        if guest!=old_guest:
            raise ValueError("existing V51 guest text base shifted")
        if index!=1:
            if code!=old_code:
                raise ValueError("previous Wii original text modified")
        else:
            if len(code)!=len(old_code):
                raise ValueError("V51 OSInit section size changed")
            off=OSINIT_CALL-guest
            expected=bytearray(old_code)
            if expected[off:off+12]!=struct.pack(">III",SC,BLR,NOP):
                raise ValueError("V51 EXI call seam/padding not synthetic")
            expected[off:off+4]=original_call
            expected[off+4:off+12]=struct.pack(">II",SC,BLR)
            if code!=expected:
                raise ValueError("V52 changed unrelated OSInit instructions")
    if new_text[6][0]!=DBINIT or old_text[6][0]!=DBINIT:
        raise ValueError("V52 DBInit/EXI region guest address changed")
    code=new_text[6][1]
    previous=old_text[6][1]
    if (code[:len(previous)]!=previous or len(previous)!=DEBUG+8-DBINIT or
        code[DEBUG-DBINIT:DEBUG-DBINIT+8]!=struct.pack(">II",SC,BLR)):
        raise ValueError("V52 modified original DBInit or synthetic debug callback")
    if code[len(previous):EXI-DBINIT]!=struct.pack(">I",NOP)*((EXI-DBINIT-len(previous))//4):
        raise ValueError("V52 EXI padding is not explicitly synthetic NOPs")
    if code[EXI-DBINIT:STOP-DBINIT]!=original_exi:
        raise ValueError("V52 original EXI code differs from owner DOL")
    if code[STOP-DBINIT:]!=struct.pack(">II",SC,BLR):
        raise ValueError("V52 missing explicit EXI test-only terminal")
    if locate(actual,OSINIT_GUARD,8)!=locate(actual,OSINIT_CALL,12)+4:
        raise ValueError("OSInit post-EXI guard moved")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    args=p.parse_args()
    verify(args.private_fixture.read_bytes(),args.owner_original_dol)
    print("PASS: V52 original EXI prefix, NOP gap, DOL sections and no-overwrite geometry")
