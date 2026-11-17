#!/usr/bin/env python3
"""V50 original Wii continuous __start/OSInit -> native __OSContextInit.

All original PowerPC instructions come only from the owner's SHA-pinned DOL.
The context exception handler remains a non-executed synthetic NOP address.
DBPrintf is still a test-only callback. Stop before the next OSInit service.
"""
from __future__ import annotations
import argparse
import struct
from pathlib import Path
from make_start_to_irq_return_v49 import make as make_v49,OSINIT_STOP as OLD_STOP,START
from make_start_to_module_v44 import locate
from make_start_to_vectorcopy_v38 import word
from make_osinit_execparams_v28 import text_at,SC,BLR,NOP
from make_alarm_v47 import call_target

CONTEXT=0x80522EB8
CONTEXT_END=0x80522F00
STOP=OLD_STOP+4
SETEXC=0x80520E9C
DBPRINTF=0x804E50B8
UNEXECUTED_HANDLER=0x80522E34

def make(owner:Path)->bytes:
    prior=make_v49(owner)
    raw=owner.read_bytes()
    call=text_at(raw,OLD_STOP,4)
    context=text_at(raw,CONTEXT,CONTEXT_END-CONTEXT)
    if (call_target(call,OLD_STOP,OLD_STOP)!=CONTEXT or
        len(context)!=0x48 or word(context,0x44)!=BLR or
        call_target(context,CONTEXT+0x18,CONTEXT)!=SETEXC or
        call_target(context,CONTEXT+0x34,CONTEXT)!=DBPRINTF):
        raise ValueError("owner original Wii OSContextInit call graph changed")
    os_at=locate(prior,OLD_STOP,12)
    if prior[os_at:os_at+12]!=struct.pack(">III",SC,BLR,NOP):
        raise ValueError("V49 original OSInit post-interrupt stop modified")
    context_at=locate(prior,CONTEXT,len(context))
    if prior[context_at:context_at+len(context)]!=struct.pack(">I",NOP)*(len(context)//4):
        raise ValueError("V50 context initializer overlaps previously verified native PPC")
    handler_at=locate(prior,UNEXECUTED_HANDLER,4)
    if word(prior,handler_at)!=NOP:
        raise ValueError("unexecuted owner context exception handler not synthetic NOP")
    out=bytearray(prior)
    out[os_at:os_at+4]=call
    out[os_at+4:os_at+12]=struct.pack(">II",SC,BLR)
    out[context_at:context_at+len(context)]=context
    if out[:256]!=prior[:256] or word(out,0xE0)!=START:
        raise ValueError("V50 owner private DOL header/entry changed")
    return bytes(out)

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("owner_original_dol",type=Path)
    p.add_argument("private_fixture",type=Path)
    a=p.parse_args()
    if a.private_fixture.exists() or a.private_fixture.is_symlink():
        p.error("refusing to overwrite owner-private original Wii test image")
    a.private_fixture.write_bytes(make(a.owner_original_dol))
    print("PASS: private original Wii V50 continuous __OSContextInit fixture built")
