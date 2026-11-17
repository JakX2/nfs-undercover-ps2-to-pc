#!/usr/bin/env python3
"""V49 continuous original Wii __OSInterruptInit epilogue returning to OSInit.

Reuses V48 authenticated SetInterruptMask and genuine __OSRestoreInterrupts
plus __OSSetExceptionHandler. All new PowerPC comes from the pinned owner DOL,
never from checked-in proprietary instructions. Stop is already at OSInit BC.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_irq_mask_v48 import make as make_v48,STOP as PREV_STOP
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target

INTERRUPT_END=0x805266E0
OSINIT_STOP=0x805208BC
RESTORE=0x805265D4
SETEXC=0x80520E9C
START=0x8000403C

def make(owner:Path)->bytes:
    prior=make_v48(owner)  # inherits exact SHA-pinned owner Wii code
    raw=owner.read_bytes()
    continuation=text_at(raw,PREV_STOP,INTERRUPT_END-PREV_STOP)
    restore=text_at(raw,RESTORE,0x24)
    if len(continuation)!=0x34 or len(restore)!=0x24:
        raise ValueError("original Wii IRQ epilogue/restore PPC length changed")
    if (call_target(continuation,0x805266B0,PREV_STOP)!=RESTORE or
        call_target(continuation,0x805266C0,PREV_STOP)!=SETEXC or
        word(continuation,len(continuation)-4)!=BLR or
        word(restore,len(restore)-4)!=BLR):
        raise ValueError("owner Wii interrupt-restore/handler guest BL graph differs")
    at=locate(prior,PREV_STOP,len(continuation))
    if prior[at:at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V48 bounded IRQ test stop modified")
    if prior[at+8:at+len(continuation)]!=struct.pack(">I",NOP)*((len(continuation)-8)//4):
        raise ValueError("original interrupt return would overwrite verified text")
    restore_at=locate(prior,RESTORE,len(restore))
    if prior[restore_at:restore_at+len(restore)]!=restore:
        raise ValueError("original Wii OSRestoreInterrupts helper not inherited")
    os_at=locate(prior,OSINIT_STOP,8)
    if prior[os_at:os_at+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("OSInit post-IRQ test-only stop was removed")
    out=bytearray(prior)
    out[at:at+len(continuation)]=continuation
    if out[:256]!=prior[:256] or word(out,0xE0)!=START:
        raise ValueError("V49 modified owner private DOL metadata")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing overwrite of owner-private Wii output")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: owner-private continuous original V49 interrupt return fixture constructed")
