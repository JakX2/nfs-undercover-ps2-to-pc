#!/usr/bin/env python3
"""Build a private, bounded original-code Wii OSInit -> L1 cache-init test.

All real PPC words are copied from an owner-original SHA-pinned Wii DOL;
only the terminal SC/BLR is synthetic, and the game-derived image stays local.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_context_v58 import make as inherited, NEW_STOP as OSINIT_STOP, OSINIT, NOP
from make_alarm_v47 import original_text, call_target, be32, SC, BLR

CACHE = 0x80522540
CACHE_STOP = 0x80522594  # before PPCMfl2cr / L2 state machine
IC_ENABLE = 0x805223BC
DC_ENABLE = 0x80522280
MFHID0 = 0x804B7920
DBPRINTF = 0x804E50B8


def make(owner: Path) -> bytes:
    previous = bytearray(inherited(owner))
    original = owner.read_bytes()
    call = original_text(original, OSINIT_STOP, 4)
    prefix = original_text(original, CACHE, CACHE_STOP-CACHE)
    ic = original_text(original, IC_ENABLE, 0x14)
    dc = original_text(original, DC_ENABLE, 0x14)
    if (call_target(call, OSINIT_STOP, OSINIT_STOP) != CACHE or
        len(prefix) != 0x54 or len(ic) != 0x14 or len(dc) != 0x14 or
        call_target(prefix,CACHE+0x1c,CACHE)!=MFHID0 or
        call_target(prefix,CACHE+0x38,CACHE)!=MFHID0 or
        call_target(prefix,CACHE+0x28,CACHE)!=IC_ENABLE or
        call_target(prefix,CACHE+0x44,CACHE)!=DC_ENABLE or
        call_target(prefix,CACHE+0x34,CACHE)!=DBPRINTF or
        call_target(prefix,CACHE+0x50,CACHE)!=DBPRINTF or
        be32(ic,len(ic)-4)!=BLR or be32(dc,len(dc)-4)!=BLR):
        raise ValueError('V59 original Wii L1 cache initialization callgraph changed')
    off, base, length = (be32(previous,p) for p in (0,0x48,0x90))
    if (base!=OSINIT or off<0x100 or off+length>len(previous) or
        not(OSINIT_STOP>=base and CACHE_STOP+4<=base+length)):
        raise ValueError('V59 private first text segment geometry changed')
    for pc, words in ((OSINIT_STOP,call),(CACHE,prefix),(IC_ENABLE,ic),(DC_ENABLE,dc)):
        where=off+pc-base
        if pc==OSINIT_STOP:
            if be32(previous,where)!=SC or be32(previous,where+4)!=BLR:
                raise ValueError('V59 missing inherited OSInit synthetic stop')
        elif any(be32(previous,where+i)!=NOP for i in range(0,len(words),4)):
            raise ValueError('V59 refuses overwrite of non-synthetic private instruction')
        previous[where:where+len(words)] = words
    dest=off+CACHE_STOP-base
    if be32(previous,dest)!=NOP or be32(previous,dest+4)!=NOP:
        raise ValueError('V59 missing synthetic stop padding before L2 path')
    struct.pack_into('>II',previous,dest,SC,BLR)
    return bytes(previous)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_original_wii_dol',type=Path)
    ap.add_argument('new_private_test_dol',type=Path)
    args=ap.parse_args()
    if args.new_private_test_dol.exists():ap.error('refuse to overwrite private DOL')
    args.new_private_test_dol.write_bytes(make(args.owner_original_wii_dol))
    print('PASS: V59 original Wii L1 cache initializer inserted privately')
