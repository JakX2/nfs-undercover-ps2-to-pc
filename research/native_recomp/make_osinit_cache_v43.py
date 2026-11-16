#!/usr/bin/env python3
"""Private Wii OSExceptionInit slice including original cache maintenance loops.

SHA-pinned owner DOL provides every PPC instruction at its original address.
This script creates a strictly private image; only this source is distributable.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_vectorcopy_v42 import make as make_v42, CACHE_STOP as PREVIOUS_STOP, FIRST_DEBUG, SECOND_DEBUG
from make_osinit_execparams_v28 import text_at, target, SC, BLR
from make_osinit_hid4_v30 import be32, OSINIT

FIRST_CACHE=0x80522320
FIRST_CACHE_LEN=0x2C
SECOND_CACHE=0x80522378
SECOND_CACHE_LEN=0x34
END_STOP=0x80520DB8


def make(owner: Path) -> bytes:
    image=bytearray(make_v42(owner))
    source=owner.read_bytes()  # SHA pinned by inherited builder
    continuation=text_at(source,PREVIOUS_STOP,END_STOP-PREVIOUS_STOP)
    dc=text_at(source,FIRST_CACHE,FIRST_CACHE_LEN)
    ic=text_at(source,SECOND_CACHE,SECOND_CACHE_LEN)
    if target(be32(continuation,0),PREVIOUS_STOP,True)!=FIRST_CACHE:
        raise ValueError('original data cache call target changed')
    if target(be32(continuation,END_STOP-PREVIOUS_STOP-4),END_STOP-4,True)!=SECOND_CACHE:
        raise ValueError('original instruction cache call target changed')
    if be32(dc,FIRST_CACHE_LEN-4)!=BLR or be32(ic,SECOND_CACHE_LEN-4)!=BLR:
        raise ValueError('original cache helper return opcode changed')
    if be32(dc,0x1c)>>26 != 31 or be32(ic,0x1c)>>26 != 31:
        raise ValueError('original cache-line instruction missing')
    off,guest,length=(be32(image,p) for p in (0,0x48,0x90))
    if guest != OSINIT or not off>=0x100 or not END_STOP+8<=guest+length:
        raise ValueError('V42 test image does not map original exception/cache code')
    if be32(image,off+PREVIOUS_STOP-guest)!=SC:
        raise ValueError('prior cache stop changed')
    for base,raw in ((FIRST_CACHE,dc),(SECOND_CACHE,ic)):
        where=off+base-guest
        for i in range(0,len(raw),4):
            if be32(image,where+i)!=0x60000000:
                raise ValueError('cache helper conflicts with owner-original existing private test code')
        image[where:where+len(raw)]=raw
    image[off+PREVIOUS_STOP-guest:off+END_STOP-guest]=continuation
    struct.pack_into('>II',image,off+END_STOP-guest,SC,BLR)
    return bytes(image)


if __name__=='__main__':
    arg=argparse.ArgumentParser()
    arg.add_argument('owner_dol',type=Path)
    arg.add_argument('private_destination',type=Path)
    a=arg.parse_args()
    if a.private_destination.exists():arg.error('refusing to overwrite existing private DOL')
    a.private_destination.write_bytes(make(a.owner_dol))
    print('PASS: V43 SHA-pinned original Wii cache functions included privately')
