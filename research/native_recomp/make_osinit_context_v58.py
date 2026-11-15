#!/usr/bin/env python3
"""Build a private, original-code-backed Wii OSInit -> __OSContextInit fixture.

Do not publish the derived DOL: original PPC bytes come only from the
SHA-pinned owner's Wii executable. The only substituted instruction is the
synthetic stop after the genuine original context initializer returns.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_interrupt_return_v57 import make as v57, OSINIT_STOP as OLD_STOP
from make_alarm_v47 import original_text, call_target, be32, SC, BLR

CONTEXT = 0x80522EB8
CONTEXT_END = 0x80522F00
NEW_STOP = OLD_STOP + 4
OSINIT = 0x80520670
NOP = 0x60000000
SET_HANDLER = 0x80520E9C
DBPRINTF = 0x804E50B8


def make(owner: Path) -> bytes:
    previous = bytearray(v57(owner))
    raw = owner.read_bytes()
    original_call = original_text(raw, OLD_STOP, 4)
    context = original_text(raw, CONTEXT, CONTEXT_END-CONTEXT)
    if (call_target(original_call, OLD_STOP, OLD_STOP) != CONTEXT or
        len(context) != 0x48 or
        call_target(context, CONTEXT+0x18, CONTEXT) != SET_HANDLER or
        call_target(context, CONTEXT+0x34, CONTEXT) != DBPRINTF or
        be32(context,len(context)-4) != BLR):
        raise ValueError('V58 source-backed OSContextInit call graph changed')
    offset, base, length = (be32(previous, a) for a in (0,0x48,0x90))
    if (base != OSINIT or offset < 0x100 or offset+length > len(previous) or
        OLD_STOP < base or CONTEXT_END > base+length):
        raise ValueError('V58 original OSInit text layout changed')
    old = offset + OLD_STOP-base
    new = offset + CONTEXT-base
    if (be32(previous,old) != SC or be32(previous,old+4) != BLR or
        be32(previous,old+8) != NOP or
        any(be32(previous,new+i) != NOP for i in range(0,len(context),4))):
        raise ValueError('V58 refused to replace non-synthetic private guest words')
    previous[old:old+4] = original_call
    struct.pack_into('>II',previous,offset+NEW_STOP-base,SC,BLR)
    previous[new:new+len(context)] = context
    return bytes(previous)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('owner_original_wii_dol',type=Path)
    parser.add_argument('new_private_dol',type=Path)
    args = parser.parse_args()
    if args.new_private_dol.exists():
        parser.error('refusing to overwrite private output')
    args.new_private_dol.write_bytes(make(args.owner_original_wii_dol))
    print('PASS: V58 SHA-pinned original OSContextInit inserted privately')
