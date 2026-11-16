#!/usr/bin/env python3
"""Private original Wii alarm startup fixture. No game instruction bytes distributed.

The original Wii DOL is read only after SHA-256 validation, and extracted
instructions are written only to a private temporary image by the owner.
"""
import argparse
import hashlib
import struct
from pathlib import Path

SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ALARM = 0x805210CC
GET = 0x80520EB0
SET = 0x80520E9C
SHUTDOWN = 0x80527B4C
STOP = 0x80004900  # Synthetic test-only return target
SC, BLR = 0x44000002, 0x4E800020
LAYOUT = ((ALARM, 0x58), (SET, 0x24), (SHUTDOWN, 0x88))


def be32(data: bytes, position: int) -> int:
    return struct.unpack_from('>I', data, position)[0]


def original_text(raw: bytes, address: int, size: int) -> bytes:
    if not size or size % 4 or address % 4 or len(raw) < 0x100:
        raise ValueError('invalid Wii DOL text request')
    for i in range(7):
        offset, base, n = (be32(raw, j+4*i) for j in (0, 0x48, 0x90))
        if n and base <= address and address+size <= base+n:
            at = offset + address-base
            if offset < 0x100 or at+size > len(raw):
                raise ValueError('truncated original text section')
            return raw[at:at+size]
    raise ValueError('original PowerPC body is absent from DOL')


def call_target(raw: bytes, address: int, start: int) -> int:
    w = be32(raw, address-start)
    if w >> 26 != 18 or (w & 1) != 1:
        raise ValueError(f'original BL missing at 0x{address:08X}')
    offset = w & 0x3fffffc
    if offset & 0x2000000:
        offset -= 0x4000000
    return ((offset if w & 2 else address + offset)) & 0xffffffff


def make(owner: Path) -> bytes:
    raw = owner.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('owner-original Wii SHA-256 mismatch')
    segments = [(pc, original_text(raw, pc, size)) for pc, size in LAYOUT]
    alarm = segments[0][1]
    funcs = segments[1][1]
    shutdown = segments[2][1]
    if be32(alarm, 0) != 0x9421FFF0 or be32(alarm, 0x54) != BLR:
        raise ValueError('original Wii alarm function changed')
    for site, dest in ((ALARM+0x10, GET), (ALARM+0x38, SET),
                       (ALARM+0x44, SHUTDOWN)):
        if call_target(alarm, site, ALARM) != dest:
            raise ValueError('original alarm callgraph differs')
    if (be32(funcs, 0x10) != BLR or be32(funcs, 0x20) != BLR or
            be32(shutdown, len(shutdown)-4) != BLR):
        raise ValueError('original alarm helper return missing')
    if be32(alarm, 0x30) != 0x38600008:
        raise ValueError('alarm exception index changed')
    segments.append((STOP, struct.pack('>II', SC, BLR)))
    output = bytearray(0x100 + sum(len(data) for _, data in segments))
    position = 0x100
    for i, (address, data) in enumerate(segments):
        for h, value in ((0, position), (0x48, address), (0x90, len(data))):
            struct.pack_into('>I', output, h+4*i, value)
        output[position:position+len(data)] = data
        position += len(data)
    struct.pack_into('>I', output, 0xe0, ALARM)
    return bytes(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('owner_dol', type=Path)
    p.add_argument('private_output', type=Path)
    args = p.parse_args()
    if args.private_output.exists():
        p.error('refusing to overwrite existing private test image')
    args.private_output.write_bytes(make(args.owner_dol))
    print('PASS: V47 owner-private original Wii alarm test DOL constructed')
