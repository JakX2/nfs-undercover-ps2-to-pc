#!/usr/bin/env python3
"""Create owner-private bounded Wii DOL with real __start and __init_registers.

Original mode reads a SHA-pinned owner DOL but writes proprietary bytes only
into an explicit local output path. Do not redistribute that derived file.
Synthetic mode contains independently authored PowerPC and no game bytes.
The __init_hardware address is replaced by a synthetic sc/blr stop.
"""
import argparse
import hashlib
import struct
from pathlib import Path

OWNER_SHA256 = '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY = 0x8000403C
REG_INIT = 0x800041A8
HW_INIT = 0x800042E0
SYNTHETIC_STOP = struct.pack('>II', 0x44000002, 0x4E800020)


def extract_text(dol: bytes, address: int, length: int) -> bytes:
    if not length or length & 3:
        raise ValueError('invalid original text span')
    if len(dol) < 0x100:
        raise ValueError('DOL shorter than header')
    for i in range(7):
        offset, start, size = (struct.unpack_from('>I', dol, base + i * 4)[0]
                               for base in (0x00, 0x48, 0x90))
        if size and start <= address and address + length <= start + size:
            pos = offset + address - start
            if pos < 0x100 or pos + length > len(dol):
                raise ValueError('DOL file range exceeds available bytes')
            return dol[pos:pos + length]
    raise ValueError('requested function not in DOL text')


def branch_target(word: int, pc: int) -> int:
    if word >> 26 != 18 or not word & 1 or word & 2:
        raise ValueError('expected direct relative PowerPC BL')
    displacement = word & 0x03FFFFFC
    if displacement & 0x02000000:
        displacement -= 0x04000000
    return (pc + displacement) & 0xFFFFFFFF


def build(original: Path | None) -> bytes:
    if original is None:
        # Independently authored BLs to the same two target addresses.
        # This branch encoding is calculated, not copied from the Wii game.
        def bl(pc, dest):
            d = (dest - pc) & 0x03FFFFFC
            return struct.pack('>I', 0x48000001 | d)
        start = bl(ENTRY, REG_INIT) + bl(ENTRY + 4, HW_INIT)
        init = struct.pack('>II', 0x3860002A, 0x4E800020)  # li r3,42 ; blr
    else:
        data = original.read_bytes()
        if hashlib.sha256(data).hexdigest() != OWNER_SHA256:
            raise ValueError('wrong owner original DOL SHA256')
        start = extract_text(data, ENTRY, 8)
        init = extract_text(data, REG_INIT, 144)
        if struct.unpack_from('>I', init, len(init) - 4)[0] != 0x4E800020:
            raise ValueError('original register init not complete at BLR')
    if branch_target(struct.unpack_from('>I', start)[0], ENTRY) != REG_INIT:
        raise ValueError('first startup branch is not register initialization')
    if branch_target(struct.unpack_from('>I', start, 4)[0], ENTRY + 4) != HW_INIT:
        raise ValueError('second startup branch is not hardware initialization')
    # Distinct DOL text sections so the upstream Analyzer cannot accidentally
    # extend a function into untrusted bytes beyond these exact selected spans.
    pieces = ((ENTRY, start), (REG_INIT, init), (HW_INIT, SYNTHETIC_STOP))
    offsets = []
    end = 0x100
    for _, contents in pieces:
        offsets.append(end)
        end = (end + len(contents) + 3) & ~3
    out = bytearray(end)
    for i, ((address, body), offset) in enumerate(zip(pieces, offsets)):
        for base, value in ((0x00, offset), (0x48, address), (0x90, len(body))):
            struct.pack_into('>I', out, base + i * 4, value)
        out[offset:offset + len(body)] = body
    struct.pack_into('>I', out, 0xE0, ENTRY)
    return bytes(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--owner-dol', type=Path)
    opts = parser.parse_args()
    if opts.output.exists():
        parser.error('refusing to overwrite private or synthetic output')
    payload = build(opts.owner_dol)
    opts.output.write_bytes(payload)
    print('Generated bounded early startup test DOL:', len(payload),
          'bytes; original register init:', bool(opts.owner_dol))


if __name__ == '__main__':
    main()
