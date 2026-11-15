#!/usr/bin/env python3
"""Bounded owner-private Wii interrupt-disable continuation, never publish game bytes.

The original game DOL is SHA-256 verified by the inherited fixture. New
PowerPC instructions are copied ONLY from that private owner input.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_mmio_v52 import make as make_v52, NEXT_STOP as OLD_STOP
from make_osinit_interrupt_bridge_v51 import INTERRUPT, TIME_SECTION
from make_alarm_v47 import original_text, be32, call_target, SC, BLR

NEW_STOP = 0x80526698
DISABLE = 0x805265AC
NOP = 0x60000000


def make(owner: Path) -> bytes:
    image = bytearray(make_v52(owner))
    raw = owner.read_bytes()
    code = original_text(raw, OLD_STOP, NEW_STOP - OLD_STOP)
    if (len(code) != 0x24 or
        call_target(code, OLD_STOP, OLD_STOP) != DISABLE or
        be32(code, 0x18) >> 26 != 36):
        raise ValueError('V53 original interrupt-disable call/mask-store changed')
    # The private section layout is checked before touching any source.
    off, guest, size = (be32(image, base+4) for base in (0, 0x48, 0x90))
    if guest != TIME_SECTION or off < 0x100 or off+size > len(image):
        raise ValueError('V53 inherited time/interrupt code layout changed')
    pos = off + OLD_STOP - TIME_SECTION
    if (pos < off or pos+len(code)+8 > off+size or
        be32(image, pos) != SC or be32(image, pos+4) != BLR or
        any(be32(image, pos+i) != NOP for i in range(8, len(code)+8, 4))):
        raise ValueError('V53 refused to overwrite unexpected original or synthetic code')
    image[pos:pos+len(code)] = code
    struct.pack_into('>II', image, pos+len(code), SC, BLR)
    return bytes(image)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('original_owner_dol', type=Path)
    ap.add_argument('private_test_image', type=Path)
    args = ap.parse_args()
    if args.private_test_image.exists():
        ap.error('refusing to overwrite an existing private fixture')
    args.private_test_image.write_bytes(make(args.original_owner_dol))
    print('PASS: V53 owner-private interrupt-disable continuation fixture built')
