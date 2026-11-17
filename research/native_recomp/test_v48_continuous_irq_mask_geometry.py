#!/usr/bin/env python3
"""V48 original-only SetInterruptMask instruction and no-overwrite guard."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_irq_disable_v47 import make as make_v47,STOP as OLD_STOP,START
from make_start_to_irq_mask_v48 import STOP,SETMASK,SOURCE_LENGTH
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR

def verify(image:bytes,owner:Path)->None:
    prior=make_v47(owner)
    if len(image)!=len(prior) or image[:256]!=prior[:256] or word(image,0xe0)!=START:
        raise ValueError("V48 changed original Wii DOL header or section mapping")
    a=locate(image,OLD_STOP,STOP+8-OLD_STOP)
    b=locate(image,SETMASK,SOURCE_LENGTH)
    allowed=set(range(a,a+STOP+8-OLD_STOP))|set(range(b,b+SOURCE_LENGTH))
    for i,(old,new) in enumerate(zip(prior,image)):
        if old!=new and i not in allowed:
            raise ValueError("V48 modified previously verified native guest startup")
    raw=owner.read_bytes()
    if image[a:a+STOP-OLD_STOP]!=text_at(raw,OLD_STOP,STOP-OLD_STOP):
        raise ValueError("V48 owner original IRQ SetInterruptMask callsite altered")
    if image[a+STOP-OLD_STOP:a+STOP-OLD_STOP+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V48 following hardware service is not test-only bounded")
    if image[b:b+SOURCE_LENGTH]!=text_at(raw,SETMASK,SOURCE_LENGTH):
        raise ValueError("V48 owner original SetInterruptMask PPC instructions differ")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: original Wii V48 SetInterruptMask/code integrity and no-overwrite geometry")
