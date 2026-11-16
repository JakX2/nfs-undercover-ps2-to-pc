#!/usr/bin/env python3
"""Create an owner-private DOL for genuine Wii __OSInitSystemCall native execution.

Original instruction and system-call stub bytes are extracted locally from the
SHA-256 pinned game DOL. The distributable builder contains no original bytes.
"""
import argparse
import hashlib
import struct
from pathlib import Path

SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
SOURCE = 0x805290A8
ENTRY = 0x805290C8
END = 0x80529128
COPY = 0x80004338
FLUSH = 0x80522320
INVALIDATE = 0x80522378
STOP = 0x80004900  # synthetic termination only
SC, BLR = 0x44000002, 0x4E800020


def be32(data, i):
    return struct.unpack_from('>I', data, i)[0]


def owner_text(data, address, size):
    if not size or size % 4 or address % 4 or len(data) < 256:
        raise ValueError('invalid original Wii DOL request')
    for i in range(7):
        off, at, length = (be32(data, j+4*i) for j in (0, 0x48, 0x90))
        if length and at <= address and address+size <= at+length:
            begin = off+address-at
            if off < 256 or begin+size > len(data):
                raise ValueError('original Wii executable section out of bounds')
            return data[begin:begin+size]
    raise ValueError('original Wii instruction range is unmapped')


def branch_target(opcode, pc):
    if opcode >> 26 != 18 or not opcode & 1:
        raise ValueError('expected original PowerPC bl')
    delta = opcode & 0x03FFFFFC
    if delta & 0x02000000:
        delta -= 0x04000000
    return (delta if opcode & 2 else pc+delta) & 0xFFFFFFFF


def make(owner: Path):
    raw = owner.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('owner Wii DOL SHA-256 mismatch')
    script = owner_text(raw, SOURCE, END-SOURCE)
    copied, flushed, invalidated = (owner_text(raw, addr, count) for addr, count in
                                   ((COPY, 80), (FLUSH, 44), (INVALIDATE, 52)))
    if be32(script, ENTRY-SOURCE) != 0x9421FFF0 or be32(script, END-SOURCE-4) != BLR:
        raise ValueError('original system-call setup function incomplete')
    for call_pc, dest in ((ENTRY+0x2C, COPY), (ENTRY+0x38, FLUSH),
                          (ENTRY+0x48, INVALIDATE)):
        if branch_target(be32(script, call_pc-SOURCE), call_pc) != dest:
            raise ValueError('original system-call setup callgraph changed')
    if (be32(script, ENTRY+0x28-SOURCE) >> 26) != 31:
        raise ValueError('original setup copy size computation changed')
    if be32(script, ENTRY+0x34-SOURCE) != 0x38800100 or be32(script, ENTRY+0x44-SOURCE) != 0x38800100:
        raise ValueError('original setup cache ranges no longer 256 bytes')
    for name, body in (("memcpy", copied), ("data cache", flushed),
                       ("instruction cache", invalidated)):
        if be32(body, len(body)-4) != BLR:
            raise ValueError(f'original {name} helper return missing')
    text = [(SOURCE, script), (COPY, copied), (FLUSH, flushed),
            (INVALIDATE, invalidated), (STOP, struct.pack('>II', SC, BLR))]
    output = bytearray(256+sum(len(code) for _, code in text))
    offset = 256
    for i, (addr, code) in enumerate(text):
        for base, value in ((0, offset), (0x48, addr), (0x90, len(code))):
            struct.pack_into('>I', output, base+i*4, value)
        output[offset:offset+len(code)] = code
        offset += len(code)
    struct.pack_into('>I', output, 0xE0, ENTRY)
    return bytes(output)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('owner_dol', type=Path)
    ap.add_argument('destination_private_dol', type=Path)
    args = ap.parse_args()
    if args.destination_private_dol.exists():
        ap.error('private output already exists; refusing overwrite')
    args.destination_private_dol.write_bytes(make(args.owner_dol))
    print('PASS: V45 original Wii system-call initializer private test image built')
