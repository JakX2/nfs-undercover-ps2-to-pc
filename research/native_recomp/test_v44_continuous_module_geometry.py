#!/usr/bin/env python3
"""Original-free fail-closed V44 guest PPC/code-integrity geometry regression."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_alarm_v43 import make as make_v43
from make_start_to_module_v44 import locate,MODULE,OLD_STOP,STOP,START
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(image:bytes,owner:Path)->None:
    prior=make_v43(owner) # original DOL SHA + all earlier continuous fixtures
    if len(image)!=len(prior) or image[:256]!=prior[:256] or word(image,0xe0)!=START:
        raise ValueError("V44 changed original guest executable header/geometry")
    at=locate(image,OLD_STOP,12)
    loc=locate(image,MODULE,24)
    allowed=set(range(at,at+12))|set(range(loc,loc+24))
    for index,(old,new) in enumerate(zip(prior,image)):
        if index not in allowed and old!=new:
            raise ValueError("V44 modified earlier verified startup/handler code")
    if image[at:at+4]!=text_at(owner.read_bytes(),OLD_STOP,4) or image[at+4:at+12]!=struct.pack(">II",SC,BLR):
        raise ValueError("V44 original module call/next test-only OS stop changed")
    if image[loc:loc+24]!=text_at(owner.read_bytes(),MODULE,24):
        raise ValueError("V44 SHA-authenticated original module PPC differs")
    if prior[loc:loc+24]!=struct.pack(">I",NOP)*6:
        raise ValueError("V44 original module code overwritten a nonempty prior function")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: V44 original Wii module PPC and no-overwrite geometry")
