#!/usr/bin/env python3
"""Owner-local original Wii ICEnable/DCEnable or independent PPC fixtures.

V20's two synthetic cache-enable endpoints become genuine original code, using
only user-provided DOL bytes in private outputs. No copied game code included.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from make_cache_slice_v20 import (
    make as make_v20, DC_ENABLE, IC_ENABLE, IC, CACHE,
    spr, word,
)
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text

SIZE = 20
HID0 = 1008
BLR = 0x4E800020
SYNC = 0x7C0004AC
ISYNC = 0x4C00012C


def _be32(data, addr):
    return struct.unpack_from('>I', data, addr)[0]


def _spr_number(insn):
    return (((insn >> 11) & 31) << 5) | ((insn >> 16) & 31)


def _check_enable(body, mask, barrier):
    if len(body) != SIZE:
        raise ValueError('incomplete IC/DC enable function')
    a, read, op, write, tail = struct.unpack('>5I', body)
    if a != barrier or tail != BLR:
        raise ValueError('cache enable barrier/return corrupted')
    if read >> 26 != 31 or (read >> 1) & 1023 != 339 or _spr_number(read) != HID0:
        raise ValueError('cache enable HID0 mfspr corrupted')
    if write >> 26 != 31 or (write >> 1) & 1023 != 467 or _spr_number(write) != HID0:
        raise ValueError('cache enable HID0 mtspr corrupted')
    rd = (read >> 21) & 31
    rs = (write >> 21) & 31
    if rd != rs:
        raise ValueError('HID0 read and write do not use the same GPR')
    if op >> 26 != 24 or (op >> 21) & 31 != rd or (op >> 16) & 31 != rd or (op & 0xFFFF) != mask:
        raise ValueError('cache enable ORI operand/mask corrupted')


def synthetic(enable_ic):
    # Independently assembled PPC: distinct registers from original, same
    # guest-visible semantics. The order is unlike the original DOL source.
    reg = 6 if enable_ic else 5
    barrier = ISYNC if enable_ic else SYNC
    mask = 0x8000 if enable_ic else 0x4000
    op = (24 << 26) | (reg << 21) | (reg << 16) | mask
    return b''.join(word(w) for w in (barrier, spr(reg, HID0, 339), op,
                                      spr(reg, HID0, 467), BLR))


def make(owner: Path | None):
    base = make_v20(owner)
    if owner is not None:
        source = owner.read_bytes()
        if hashlib.sha256(source).hexdigest() != ORIGINAL_SHA:
            raise ValueError('owner DOL SHA-256 does not match verified copy')
        dc = get_text(source, DC_ENABLE, SIZE)
        ic = get_text(source, IC_ENABLE, SIZE)
    else:
        dc, ic = synthetic(False), synthetic(True)
    _check_enable(dc, 0x4000, SYNC)
    _check_enable(ic, 0x8000, ISYNC)
    regions = []
    for i in range(7):
        offset, addr, size = (_be32(base, b + 4*i) for b in (0, 0x48, 0x90))
        if offset == 0 or size == 0:
            raise ValueError('missing inherited Wii DOL section')
        payload = base[offset:offset+size]
        if i == 3:
            if addr != DC_ENABLE or addr+size != IC_ENABLE+8:
                raise ValueError('unexpected V20 IC/DC test section boundaries')
            # Include full ICEnable, which is 12 bytes longer than the V20 sc/blr
            # placeholder, without touching the original ICFlashInvalidate body.
            region = bytearray(payload + b'\0' * (SIZE - 8))
            region[:SIZE] = dc
            region[IC_ENABLE - DC_ENABLE:IC_ENABLE - DC_ENABLE + SIZE] = ic
            payload = bytes(region)
        regions.append((addr, payload))
    length = 0x100 + sum((len(body)+3) & ~3 for _,body in regions)
    out = bytearray(length)
    at = 0x100
    for i, (addr, payload) in enumerate(regions):
        for base_off, value in ((0,at),(0x48,addr),(0x90,len(payload))):
            struct.pack_into('>I', out, base_off + i*4, value)
        out[at:at+len(payload)] = payload
        at += (len(payload)+3) & ~3
    struct.pack_into('>I', out, 0xE0, 0x8000403C)
    return bytes(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('destination', type=Path)
    ap.add_argument('--owner-dol', type=Path, default=None)
    args = ap.parse_args()
    if args.destination.exists():
        ap.error('destination already exists: refusing to overwrite generated DOL')
    args.destination.write_bytes(make(args.owner_dol))
    print('V21 private DOL slice created; owner =', bool(args.owner_dol))
