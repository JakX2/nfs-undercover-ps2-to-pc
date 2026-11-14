#!/usr/bin/env python3
"""Build a private DOL containing genuine owner-original Wii OS exec-param code.

All PowerPC instruction bytes are extracted locally from a SHA-pinned DOL.
This original-free script never publishes or prints extracted code.
"""
import argparse
import hashlib
import struct
from pathlib import Path

ORIGINAL_SHA = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY = 0x80523B1C
COPY = 0x80004338
STOP = 0x80004900
NOP = 0x60000000
BLR = 0x4E800020
SC = 0x44000002


def word(block, at):
    return struct.unpack_from('>I', block, at)[0]


def get_original_text(raw, address, count):
    if len(raw) < 0x100 or count <= 0 or count % 4 or address % 4:
        raise ValueError('invalid DOL section or instruction alignment')
    for index in range(7):
        offset, base, size = (word(raw, x + 4 * index) for x in (0, 0x48, 0x90))
        if size and base <= address and address + count <= base + size:
            where = offset + address - base
            if offset < 0x100 or where + count > len(raw):
                raise ValueError('original DOL section truncated')
            return raw[where:where + count]
    raise ValueError('original guest function not fully mapped')


def check_source(helper, copier):
    if len(helper) != 36 or len(copier) != 80:
        raise ValueError('original helper length mismatch')
    if word(helper, 32) != BLR or word(copier, 76) != BLR:
        raise ValueError('expected original PPC return missing')
    # The two paths: low pointer -> zero destination; valid pointer -> tail
    # branch to original memcpy with exactly 28 bytes. Never patch game bytes.
    if word(helper, 0) != 0x3CA08000 or word(helper, 4) != 0x808530F0:
        raise ValueError('unexpected Wii low-memory exec-params source')
    if word(helper, 16) != 0x38A0001C or word(helper, 24) != 0x38000000:
        raise ValueError('unexpected exec-params copy length or zero path')
    if word(helper, 28) != 0x90030000:
        raise ValueError('exec-params zero write changed')
    branch = word(helper, 20)
    if branch >> 26 != 18 or branch & 3:
        raise ValueError('expected unconditional nonlinking tail branch')
    displacement = branch & 0x03FFFFFC
    if displacement & 0x02000000:
        displacement -= 0x04000000
    target = (displacement if branch & 2 else ENTRY + 20 + displacement) & 0xffffffff
    if target != COPY:
        raise ValueError('original exec-params memcpy tail target changed')


def make(original):
    raw = Path(original).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError('owner-original Wii DOL SHA mismatch')
    helper = get_original_text(raw, ENTRY, 36)
    copier = get_original_text(raw, COPY, 80)
    check_source(helper, copier)
    texts = [(ENTRY, helper), (COPY, copier), (STOP, struct.pack('>II', SC, BLR))]
    result = bytearray(0x100 + sum(len(payload) for _, payload in texts))
    cursor = 0x100
    for index, (guest, payload) in enumerate(texts):
        for field, value in ((0, cursor), (0x48, guest), (0x90, len(payload))):
            struct.pack_into('>I', result, field + 4 * index, value)
        result[cursor:cursor + len(payload)] = payload
        cursor += len(payload)
    struct.pack_into('>I', result, 0xE0, ENTRY)
    return bytes(result)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('owner_dol', type=Path)
    parser.add_argument('output_private_dol', type=Path)
    args = parser.parse_args()
    if args.output_private_dol.exists():
        parser.error('refusing to overwrite existing file')
    image = make(args.owner_dol)
    args.output_private_dol.write_bytes(image)
    print('PASS: V27 private original OSGetExecParams/memcpy slice; bytes=', len(image))


if __name__ == '__main__':
    main()
