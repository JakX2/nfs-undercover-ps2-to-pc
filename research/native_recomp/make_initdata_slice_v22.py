#!/usr/bin/env python3
"""Bounded original-free constructor for an owner's PRIVATE __init_data slice.

No original Wii instructions or original table bytes are distributed here.
The owner must supply the SHA-pinned game DOL to extract the source locally.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY = 0x80004238
END = 0x8000446C
STOP = 0x80004900
TABLE = 0x80006420
TABLE_LENGTH = 0xB0
FILL = 0x80004388
FLUSH = 0x80004304
COPY = 0x80004338
SET = 0x8000443C
ORIGINAL_COPY_ROWS = 11
ORIGINAL_BSS_ROWS = 3


def be32(block, where):
    return struct.unpack_from('>I', block, where)[0]


def get_section(data, address, length):
    if len(data) < 0x100 or length <= 0 or length & 3 or address & 3:
        raise ValueError('invalid input DOL header or selected range')
    for i in range(7):
        off, base, size = (be32(data, x + i * 4) for x in (0, 0x48, 0x90))
        if size and base <= address and address + length <= base + size:
            begin = off + address-base
            if begin < 0x100 or begin + length > len(data):
                raise ValueError('original DOL section outside file')
            return data[begin:begin+length]
    raise ValueError('original text or table not in an initialized DOL text section')


def make_synthetic_table():
    """Small memory fixture exercises actual memcpy, flush, memset and __fill_mem."""
    table = bytearray(TABLE_LENGTH)
    # __init_data copy rows are <src,dest,size> in big-endian guest memory.
    struct.pack_into('>III', table, 0, 0x80031000, 0x80032000, 65)
    # sentinel at +12
    # BSS zero table begins at TABLE+0x90 with <dest,size> rows.
    struct.pack_into('>II', table, 0x90, 0x80033000, 96)
    struct.pack_into('>II', table, 0x98, 0x80033100, 7)
    return bytes(table)


def in_guest_ram(address, length):
    end = address + length
    return ((0x80000000 <= address < 0x81800000 and end <= 0x81800000)
            or (0x90000000 <= address < 0x94000000 and end <= 0x94000000))


def parse_table(table):
    if len(table) != TABLE_LENGTH:
        raise ValueError('unexpected init-data table size')
    copy = []
    for offset in range(0, 0x90, 12):
        source, dest, length = struct.unpack_from('>III', table, offset)
        if not length:
            break
        if not source or not dest or length > 0x01000000:
            raise ValueError('invalid relocation entry')
        if not in_guest_ram(source, length) or not in_guest_ram(dest, length):
            raise ValueError('relocation entry outside Wii guest RAM')
        copy.append((source, dest, length))
    else:
        raise ValueError('missing relocation terminator')
    zero = []
    for offset in range(0x90, TABLE_LENGTH, 8):
        dest, length = struct.unpack_from('>II', table, offset)
        if not length:
            break
        if not dest or length > 0x01000000 or not in_guest_ram(dest, length):
            raise ValueError('invalid zero-initialization entry')
        zero.append((dest, length))
    else:
        raise ValueError('missing zero table terminator')
    return copy, zero


def check_code(code):
    if len(code) != END - ENTRY:
        raise ValueError('truncated original init section')
    funcs = {ENTRY: 168, FLUSH: 52, COPY: 80, FILL: 180, SET: 48}
    for addr, length in funcs.items():
        if be32(code, addr-ENTRY+length-4) != 0x4e800020:
            raise ValueError(f'original PPC function at {addr:08x} has no final blr')
    # All four direct BL callsites in the source are pinned to expected helpers.
    expected = {ENTRY+72:COPY, ENTRY+84:FLUSH, ENTRY+128:SET, SET+20:FILL}
    for pc, target in expected.items():
        raw = be32(code, pc - ENTRY)
        if raw >> 26 != 18 or (raw & 3) != 1:
            raise ValueError('unexpected init-data branch instruction')
        delta = raw & 0x03fffffc
        if delta & 0x02000000:
            delta -= 0x04000000
        if (pc + delta) & 0xffffffff != target:
            raise ValueError('unexpected init-data helper call target')


def make(owner_path: Path, table_mode: str):
    if table_mode not in ('original', 'synthetic'):
        raise ValueError('unknown table mode')
    original = owner_path.read_bytes()
    if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
        raise ValueError('original Wii DOL SHA-256 mismatch')
    code = get_section(original, ENTRY, END - ENTRY)
    check_code(code)
    table = get_section(original, TABLE, TABLE_LENGTH)
    originals = parse_table(table)
    if len(originals[0]) != ORIGINAL_COPY_ROWS or len(originals[1]) != ORIGINAL_BSS_ROWS:
        raise ValueError('owner DOL initialization table shape differs from verified original')
    if any(a != b for a, b, _ in originals[0]):
        raise ValueError('verified owner DOL expects in-place copy table')
    if table_mode == 'synthetic':
        table = make_synthetic_table()
        assert len(parse_table(table)[0]) == 1
    # 2 PPC text sections, one data section. This is NOT a full Wii image.
    texts = [(ENTRY, code), (STOP, struct.pack('>II', 0x44000002, 0x4e800020))]
    datas = [(TABLE, table)]
    result = bytearray(0x100 + sum(len(x) for _, x in texts + datas))
    at = 0x100
    for i, (guest, payload) in enumerate(texts):
        for start, value in ((0, at), (0x48, guest), (0x90, len(payload))):
            struct.pack_into('>I', result, start + 4*i, value)
        result[at:at+len(payload)] = payload
        at += len(payload)
    for i, (guest, payload) in enumerate(datas):
        for start, value in ((0x1c, at), (0x64, guest), (0xac, len(payload))):
            struct.pack_into('>I', result, start+4*i, value)
        result[at:at+len(payload)] = payload
        at += len(payload)
    struct.pack_into('>I', result, 0xe0, ENTRY)
    return bytes(result)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('original_owner_dol', type=Path)
    ap.add_argument('destination', type=Path)
    ap.add_argument('--table-mode', choices=['original', 'synthetic'], default='synthetic')
    args = ap.parse_args()
    if args.destination.exists():
        ap.error('refusing to overwrite existing private test DOL')
    args.destination.write_bytes(make(args.original_owner_dol, args.table_mode))
    print('V22 private initialization test DOL created; table mode:', args.table_mode)
