#!/usr/bin/env python3
"""V47 protected owner-PPC interrupt disable/mask instruction geometry."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_interrupt_mmio_v46 import make as make_v46,NEW_STOP as OLD_STOP
from make_start_to_irq_disable_v47 import STOP,START
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR

def verify(image:bytes,owner:Path)->None:
    old=make_v46(owner)
    if len(image)!=len(old) or image[:256]!=old[:256] or word(image,0xe0)!=START:
        raise ValueError("V47 original Wii executable header/sections changed")
    offset=locate(image,OLD_STOP,STOP+8-OLD_STOP)
    allowed=set(range(offset,offset+STOP+8-OLD_STOP))
    for i,(before,after) in enumerate(zip(old,image)):
        if i not in allowed and before!=after:
            raise ValueError("V47 altered previously verified continuous startup PPC")
    original=text_at(owner.read_bytes(),OLD_STOP,STOP-OLD_STOP)
    if image[offset:offset+len(original)]!=original:
        raise ValueError("V47 interrupt disable/mask PPC differs from owner")
    if image[offset+len(original):offset+len(original)+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V47 next unresolved Wii interrupt service not test-bounded")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    args=p.parse_args()
    verify(args.private_fixture.read_bytes(),args.owner_original_dol)
    print("PASS: V47 original IRQ disable/mask PPC and no-overwrite guards")
