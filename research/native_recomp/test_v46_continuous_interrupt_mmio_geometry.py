#!/usr/bin/env python3
"""Owner-original V46 interrupt MMIO PPC and no-overwrite fixture verification."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_interrupt_v45 import make as make_v45, STOP as OLD_STOP
from make_start_to_interrupt_mmio_v46 import NEW_STOP,START
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(actual:bytes,owner:Path)->None:
    previous=make_v45(owner)  # SHA-verified owner Wii code and V45 assertions
    if actual[:256]!=previous[:256] or len(actual)!=len(previous) or word(actual,0xe0)!=START:
        raise ValueError("V46 original Wii DOL header/section geometry changed")
    off=locate(actual,OLD_STOP,NEW_STOP+8-OLD_STOP)
    allowed=set(range(off,off+NEW_STOP+8-OLD_STOP))
    for i,(old,new) in enumerate(zip(previous,actual)):
        if i not in allowed and old!=new:
            raise ValueError("V46 overwrote a previously verified original Wii instruction")
    code=text_at(owner.read_bytes(),OLD_STOP,NEW_STOP-OLD_STOP)
    if actual[off:off+len(code)]!=code:
        raise ValueError("V46 MMIO and interrupt-mask PPC differs from owner")
    if actual[off+len(code):off+len(code)+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V46 next original interrupt hardware service not bounded")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: V46 original Wii interrupt MMIO PPC, no-overwrite and guarded stop")
