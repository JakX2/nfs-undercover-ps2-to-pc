#!/usr/bin/env python3
"""Private continuous Wii V46 interrupt low-memory/MMIO prefix fixture.

Extends SHA-authenticated native __start -> OSInit -> __OSInterruptInit
through the original two interrupt-controller MMIO store instructions.
This is only a bounded native verification fixture. No PI/IOS device model
is implied; test-only host callbacks observe the two writes and stop before
the next unimplemented original branch.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_interrupt_v45 import make as make_v45, STOP as OLD_STOP
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP

NEW_STOP=0x80526674
START=0x8000403C

def is_stw(insn:int,src:int,base:int,disp:int)->bool:
    return (insn>>26==36 and (insn>>21)&31==src and
            (insn>>16)&31==base and (insn&0xffff)==disp)

def make(owner:Path)->bytes:
    previous=make_v45(owner)
    raw=owner.read_bytes()
    continuation=text_at(raw,OLD_STOP,NEW_STOP-OLD_STOP)
    if (len(continuation)!=0x28 or
        not is_stw(word(continuation,0x20),5,4,0x3004) or
        not is_stw(word(continuation,0x24),0,3,0x34)):
        raise ValueError("V46 original Wii interrupt hardware write PCs changed")
    off=locate(previous,OLD_STOP,len(continuation)+8)
    if previous[off:off+8]!=struct.pack(">II",SC,BLR):
        raise ValueError("V45 original IRQ table test stop unexpectedly changed")
    if previous[off+8:off+len(continuation)+8]!=struct.pack(">I",NOP)*(len(continuation)//4):
        raise ValueError("V46 original MMIO code would overlap prior PPC")
    result=bytearray(previous)
    result[off:off+len(continuation)]=continuation
    result[off+len(continuation):off+len(continuation)+8]=struct.pack(">II",SC,BLR)
    if result[:256]!=previous[:256] or word(result,0xe0)!=START:
        raise ValueError("V46 unexpectedly modified Wii DOL header/entry")
    return bytes(result)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing owner-private fixture overwrite")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: private V46 continuous original IRQ MMIO write fixture constructed")
