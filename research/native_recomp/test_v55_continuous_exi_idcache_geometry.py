#!/usr/bin/env python3
"""Independent exact V55 old-to-new Wii DOL allowed-ranges/no-overwrite oracle."""
from __future__ import annotations
import argparse,struct
from pathlib import Path
from make_start_to_exi_handlers_v54 import make as make_v54
from make_start_to_exi_idcache_v55 import (
    EXI,OLD_STOP,STOP,ID,PREFIX_END,SLOW_STOP,
    EPILOGUE,EPILOGUE_END,START,verify_original,
)
from make_start_to_epilogue_v41 import sections_of
from make_osinit_execparams_v28 import NOP,SC,BLR
from make_start_to_vectorcopy_v38 import word

def verify(actual:bytes,owner:Path)->None:
    prev=make_v54(owner)
    exi,prefix,epilogue=verify_original(owner.read_bytes())
    old,olddata=sections_of(prev)
    new,newdata=sections_of(actual)
    if (word(actual,0xE0)!=START or newdata!=olddata or
        len(old)!=7 or len(new)!=7 or actual[0xE0:0x100]!=prev[0xE0:0x100]):
        raise ValueError("V55 DOL entry/section arrangement changed")
    for i,((guest,oldcode),(newguest,newcode)) in enumerate(zip(old,new)):
        if newguest!=guest:
            raise ValueError("V55 relocated old guest text segment")
        expected=bytearray(oldcode)
        if i==6:
            if expected[EXI-guest:OLD_STOP-guest]!=exi[:OLD_STOP-EXI] or expected[OLD_STOP-guest:]!=struct.pack(">II",SC,BLR):
                raise ValueError("V55 inherited EXI prefix/test stop changed")
            expected[OLD_STOP-guest:]=exi[OLD_STOP-EXI:]+struct.pack(">II",SC,BLR)
            expected.extend(struct.pack(">I",NOP)*((ID-(guest+len(expected)))//4))
            expected.extend(prefix+struct.pack(">II",SC,BLR))
            expected.extend(struct.pack(">I",NOP)*((EPILOGUE-(guest+len(expected)))//4))
            expected.extend(epilogue)
            if len(expected)!=EPILOGUE_END-guest:
                raise ValueError("V55 EXIGetID EPILOGUE bound invalid")
        if expected!=newcode:
            raise ValueError("V55 translated source overwrote prior original Wii instructions")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_image",type=Path)
    p.add_argument("owner_dol",type=Path)
    a=p.parse_args()
    verify(a.private_image.read_bytes(),a.owner_dol)
    print("PASS: original V55 EXIGetID cached return and test-only slow probe branch geometry")
