#!/usr/bin/env python3
"""V48 continuous native __start into original Wii SetInterruptMask seven-bank loop.

The original Wii PPC instructions come only from the SHA-256 pinned owner DOL.
This image is produced privately and stops at 0x805266AC before the next
unimplemented IRQ initialization service. Never publish owner game bytes.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path

from make_start_to_irq_disable_v47 import make as make_v47,STOP as OLD_STOP,START
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target
from make_setmask_v54 import ENTRY as SETMASK,STOP as SETMASK_END

STOP=0x805266AC
CALL=0x805266A0
IRQ=0x8052661C
SOURCE_LENGTH=SETMASK_END-SETMASK

def make(owner:Path)->bytes:
    prior=make_v47(owner)  # authentic owner SHA, 15-vector/syscall/alarm/MMIO/IRQ
    raw=owner.read_bytes()
    continuation=text_at(raw,OLD_STOP,STOP-OLD_STOP)
    setmask=text_at(raw,SETMASK,SOURCE_LENGTH)
    if len(continuation)!=0x14 or len(setmask)!=0x25c:
        raise ValueError("original Wii SetInterruptMask slice length changed")
    if call_target(continuation,CALL,OLD_STOP)!=SETMASK or word(setmask,0x258)!=BLR:
        raise ValueError("original Wii IRQ SetInterruptMask BL graph or final return differs")
    for pc in (0x80526708,0x80526778,0x805267b8,0x805267e4,
               0x80526828,0x8052686c,0x805268a0,0x80526938):
        if word(setmask,pc-SETMASK)!=BLR:
            raise ValueError("owner original SetInterruptMask guest exit changed")
    before=locate(prior,OLD_STOP,len(continuation)+8)
    if prior[before:before+8]!=struct.pack(">II",SC,BLR) or (
       prior[before+8:before+len(continuation)+8] !=
       struct.pack(">I",NOP)*(len(continuation)//4)):
        raise ValueError("V47 original IRQ prefix test stop/padding changed")
    at=locate(prior,SETMASK,SOURCE_LENGTH)
    if prior[at:at+SOURCE_LENGTH]!=struct.pack(">I",NOP)*(SOURCE_LENGTH//4):
        raise ValueError("V48 cannot overwrite non-NOP original guest code")
    if before<=at<before+len(continuation)+8 or at<=before<at+SOURCE_LENGTH:
        raise ValueError("IRQ continuation overlaps original SetInterruptMask")
    out=bytearray(prior)
    out[before:before+len(continuation)]=continuation
    out[before+len(continuation):before+len(continuation)+8]=struct.pack(">II",SC,BLR)
    out[at:at+SOURCE_LENGTH]=setmask
    if out[:256]!=prior[:256] or word(out,0xE0)!=START:
        raise ValueError("V48 modified owner DOL section metadata")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing to overwrite owner-private Wii executable slice")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: private original V48 continuous Wii SetInterruptMask fixture constructed")
