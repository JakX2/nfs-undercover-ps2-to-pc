#!/usr/bin/env python3
"""Produce bounded native-startup DOL with ORIGINAL (owner mode) __init_hardware.

Only the three Wii OS service bodies are replaced by synthetic sc;blr
boundaries. Original-derived DOL slices must remain private.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
START = 0x8000403C
REGS = 0x800041A8
HARDWARE = 0x800042E0
SERVICE = (0x80520FB4, 0x8051FBB0, 0x80522540)
STOP = struct.pack('>II', 0x44000002, 0x4E800020)


def get_text(dol: bytes, address: int, length: int) -> bytes:
    if len(dol) < 256 or not length or length & 3:
        raise ValueError('bad DOL header or text span')
    for i in range(7):
        file_at, start, size = (struct.unpack_from('>I', dol, base + 4*i)[0]
                                for base in (0x00, 0x48, 0x90))
        if size and start <= address and address + length <= start + size:
            where = file_at + address - start
            if where < 256 or where + length > len(dol):
                raise ValueError('DOL section outside original file')
            return dol[where:where+length]
    raise ValueError('selected guest text address not mapped')


def bl(pc: int, target: int) -> bytes:
    delta = (target-pc) & 0xffffffff
    signed = delta if delta < 0x80000000 else delta - 0x100000000
    if signed % 4 or not -0x02000000 <= signed < 0x02000000:
        raise ValueError('branch target out of range')
    return struct.pack('>I', 0x48000001 | (delta & 0x03fffffc))


def linked_target(opcode: int, pc: int) -> int:
    if opcode >> 26 != 18 or not opcode & 1 or opcode & 2:
        raise ValueError('expected direct relative bl')
    disp = opcode & 0x03fffffc
    if disp & 0x02000000:
        disp -= 0x04000000
    return (pc+disp) & 0xffffffff


def make(owner: Path | None) -> bytes:
    if owner:
        dol = owner.read_bytes()
        if hashlib.sha256(dol).hexdigest() != ORIGINAL_SHA:
            raise ValueError('owner original DOL SHA-256 mismatch')
        start = get_text(dol, START, 8)
        registers = get_text(dol, REGS, 144)
        hardware = get_text(dol, HARDWARE, 36)
    else:
        start = bl(START, REGS) + bl(START+4, HARDWARE)
        registers = struct.pack('>II', 0x3860002a, 0x4e800020)  # li r3,42; blr
        # Independent synthetic MSR init, with r7 instead of original r0.
        words = (0x7ce000a6, 0x60e72000, 0x7ce00124, 0x7fe802a6)
        hardware = struct.pack('>4I', *words) + b''.join(
            bl(HARDWARE+16+4*i, dest) for i, dest in enumerate(SERVICE))
        hardware += struct.pack('>II', 0x7fe803a6, 0x4e800020)

    for idx, target in enumerate((REGS, HARDWARE)):
        if linked_target(struct.unpack_from('>I', start, 4*idx)[0], START+4*idx) != target:
            raise ValueError('startup branch no longer matches expected target')
    if len(registers) not in (8,144) or struct.unpack_from('>I',registers,len(registers)-4)[0]!=0x4e800020:
        raise ValueError('incomplete register initializer')
    if len(hardware) != 36 or struct.unpack_from('>I',hardware,32)[0]!=0x4e800020:
        raise ValueError('incomplete hardware initializer')
    for i, target in enumerate(SERVICE):
        if linked_target(struct.unpack_from('>I',hardware,16+4*i)[0],HARDWARE+16+4*i)!=target:
            raise ValueError('hardware OS service order/call mismatch')

    pieces = [(START,start+STOP),(REGS,registers),(HARDWARE,hardware)]
    pieces += [(pc,STOP) for pc in SERVICE]
    assert len(pieces)==6  # DOL has only seven text section slots.
    size = 256 + sum((len(body)+3)&~3 for _,body in pieces)
    output = bytearray(size)
    offset=256
    for i,(addr,body) in enumerate(pieces):
        for base,value in ((0x00,offset),(0x48,addr),(0x90,len(body))):
            struct.pack_into('>I',output,base+4*i,value)
        output[offset:offset+len(body)]=body
        offset += (len(body)+3)&~3
    struct.pack_into('>I',output,0xe0,START)
    return bytes(output)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('destination',type=Path)
    parser.add_argument('--owner-dol',type=Path,default=None)
    args=parser.parse_args()
    if args.destination.exists():
        parser.error('refusing to overwrite output')
    data=make(args.owner_dol)
    args.destination.write_bytes(data)
    print(f'V17 bounded six-function DOL {len(data)} bytes; original={bool(args.owner_dol)}')

if __name__=='__main__': main()
