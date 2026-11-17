#!/usr/bin/env python3
"""Owner-private V40 continuous Wii __start -> all 15 exception vectors.

Extend the independently verified V39 cache-loop fixture with the genuine
original Wii exception loopback and handler-table initialization. No original
guest instructions are embedded in public source or uploaded as artifacts.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct

from make_start_to_cache_v39 import make as make_v39, STOP as PREVIOUS_STOP
from make_start_to_vectorcopy_v38 import OSINIT, word
from make_osinit_vectors_v44 import NEXT_STOP as STOP, DBPRINTF
from make_osinit_execparams_v28 import text_at, target, SC, BLR

NOP = 0x60000000

def make(owner: Path) -> bytes:
    image = bytearray(make_v39(owner))  # inherits original DOL SHA and all V39 guards
    source = owner.read_bytes()
    if PREVIOUS_STOP != 0x80520DB8 or STOP != 0x80520E58:
        raise ValueError("original continuous Wii exception loop boundary changed")
    continuation = text_at(source, PREVIOUS_STOP, STOP-PREVIOUS_STOP)
    finish = text_at(source, STOP, 4)
    if (len(continuation) != 0xA0 or
        tuple(word(continuation, i) for i in (0,4,8,0x98,0x9C)) !=
        (0x3BBD0001,0x281D000F,0x4180FEE8,0x937C0000,0x4CC63182)):
        raise ValueError("original 15-vector counter/backedge/template restore changed")
    if target(word(finish,0),STOP,True) != DBPRINTF:
        raise ValueError("original exception terminal debug call target changed")
    off,guest,size=(word(image,k+4) for k in (0,0x48,0x90))
    if off<256 or guest != OSINIT or STOP+8 > guest+size:
        raise ValueError("V39 continuous OSExceptionInit section cannot cover V40")
    old=off+PREVIOUS_STOP-guest
    if image[old:old+8] != struct.pack(">II",SC,BLR):
        raise ValueError("V39 test-only guest syscall stop missing")
    # Previous stop was only a two-instruction placeholder. Every other
    # address must remain a synthetic NOP before insertion.
    for pc in range(PREVIOUS_STOP+8,STOP+8,4):
        if word(image,off+pc-guest)!=NOP:
            raise ValueError("V40 exception-loop overlaps an existing PPC fixture")
    image[old:old+len(continuation)] = continuation
    struct.pack_into(">II",image,off+STOP-guest,SC,BLR)
    return bytes(image)

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("owner_original_dol",type=Path)
    parser.add_argument("private_fixture",type=Path)
    a=parser.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        parser.error("private fixture already exists; refusing overwrite")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: V40 original 15-vector Wii startup loop fixture constructed in private scratch")
