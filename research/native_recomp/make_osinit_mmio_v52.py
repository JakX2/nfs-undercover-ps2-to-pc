#!/usr/bin/env python3
"""Owner-private original Wii OSInit interrupt-MMIO prefix fixture (V52).

Extracts all original PPC from a locally supplied, SHA-pinned Wii DOL.
Only test termination is synthetic; never distributes game instructions.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_interrupt_bridge_v51 import make as make_v51, INTERRUPT, INTERRUPT_STOP, TIME_SECTION
from make_alarm_v47 import original_text, be32, SC, BLR

NEXT_STOP=0x80526674


def make(owner: Path) -> bytes:
    inherited=bytearray(make_v51(owner))
    code=original_text(owner.read_bytes(),INTERRUPT_STOP,NEXT_STOP-INTERRUPT_STOP)
    # The owner-derived DOL's first hardware write pair is at 0x8052666c and
    # 0x80526670; the stop must be before the next original BL.
    def is_stw(inst, source, base, displacement):
        return (inst >> 26 == 36 and ((inst >> 21) & 31) == source and
                ((inst >> 16) & 31) == base and (inst & 0xFFFF) == displacement)
    if (len(code)!=0x28 or not is_stw(be32(code,0x20),5,4,0x3004) or
            not is_stw(be32(code,0x24),0,3,0x34)):
        raise ValueError('V52 interrupt-MMIO write sites do not match owner PPC')
    off,base,size=(be32(inherited,h+4) for h in (0,0x48,0x90))
    if base!=TIME_SECTION or off<256 or off+size>len(inherited):
        raise ValueError('V52 unexpected inherited private section layout')
    where=off+INTERRUPT_STOP-TIME_SECTION
    if be32(inherited,where)!=SC or be32(inherited,where+4)!=BLR:
        raise ValueError('V52 inherited synthetic stop is missing')
    if any(be32(inherited,where+i)!=0x60000000 for i in range(8,0x30,4)):
        raise ValueError('V52 would overwrite non-synthetic private instructions')
    inherited[where:where+len(code)]=code
    struct.pack_into('>II',inherited,off+NEXT_STOP-TIME_SECTION,SC,BLR)
    return bytes(inherited)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('owner_dol',type=Path)
    parser.add_argument('private_output',type=Path)
    args=parser.parse_args()
    if args.private_output.exists():
        parser.error('refusing to overwrite existing private test image')
    args.private_output.write_bytes(make(args.owner_dol))
    print('PASS: V52 owner-private original Wii interrupt-MMIO fixture created')
