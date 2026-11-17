#!/usr/bin/env python3
"""V49 owner-original IRQ return PowerPC source/no-overwrite regression."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_irq_mask_v48 import make as make_v48,STOP as PREV_STOP
from make_start_to_irq_return_v49 import INTERRUPT_END,OSINIT_STOP,START
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR

def verify(image:bytes,owner:Path)->None:
    prior=make_v48(owner)
    if len(image)!=len(prior) or image[:256]!=prior[:256] or word(image,0xE0)!=START:
        raise ValueError("V49 original DOL section metadata/entry changed")
    at=locate(image,PREV_STOP,INTERRUPT_END-PREV_STOP)
    allowed=set(range(at,at+INTERRUPT_END-PREV_STOP))
    for i,(old,new) in enumerate(zip(prior,image)):
        if i not in allowed and old!=new:
            raise ValueError("V49 overwrote prior native continuous startup PPC")
    code=text_at(owner.read_bytes(),PREV_STOP,INTERRUPT_END-PREV_STOP)
    if image[at:at+len(code)]!=code:
        raise ValueError("V49 original IRQ restore/exception handler PPC differs")
    os_at=locate(image,OSINIT_STOP,8)
    if image[os_at:os_at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V49 original OSInit fallback boundary is not synthetic")
    if prior[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V48 parent IRC stop changed unexpectedly")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: original Wii V49 IRQ epilogue and unchanged startup geometry")
