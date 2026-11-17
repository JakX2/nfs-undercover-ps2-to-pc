#!/usr/bin/env python3
"""V50 SHA-authenticated native context initializer and no-overwrite guard."""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_irq_return_v49 import make as make_v49,OSINIT_STOP as OLD_STOP,START
from make_start_to_context_v50 import CONTEXT,CONTEXT_END,STOP,UNEXECUTED_HANDLER
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

def verify(image:bytes,owner:Path)->None:
    old=make_v49(owner)
    if len(image)!=len(old) or image[:256]!=old[:256] or word(image,0xE0)!=START:
        raise ValueError("V50 changed original Wii text/data section geometry")
    a=locate(image,OLD_STOP,12)
    b=locate(image,CONTEXT,CONTEXT_END-CONTEXT)
    permitted=set(range(a,a+12))|set(range(b,b+CONTEXT_END-CONTEXT))
    for i,(x,y) in enumerate(zip(old,image)):
        if x!=y and i not in permitted:
            raise ValueError("V50 modified earlier verified guest startup PPC")
    raw=owner.read_bytes()
    if image[a:a+4]!=text_at(raw,OLD_STOP,4):
        raise ValueError("V50 authentic context BL differs from pinned owner")
    if image[a+4:a+12]!=struct.pack(">II",SC,BLR):
        raise ValueError("next original OSInit service lacks test stop")
    if image[b:b+CONTEXT_END-CONTEXT]!=text_at(raw,CONTEXT,CONTEXT_END-CONTEXT):
        raise ValueError("original Wii context initializer function differs")
    at=locate(image,UNEXECUTED_HANDLER,4)
    if word(image,at)!=NOP:
        raise ValueError("unimplemented exception handler unexpectedly executable")

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_fixture",type=Path)
    p.add_argument("owner_original_dol",type=Path)
    a=p.parse_args()
    verify(a.private_fixture.read_bytes(),a.owner_original_dol)
    print("PASS: original Wii V50 context PPC, bounded next stop and no-overwrite")
