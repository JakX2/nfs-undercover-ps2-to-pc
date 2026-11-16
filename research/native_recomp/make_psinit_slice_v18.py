#!/usr/bin/env python3
"""Original-free bounded __OSPSInit native dispatch test DOL creator.

Owner mode privately extracts verified Wii instructions, leaving original
__OSPSInit, PPCMfhid2, PPCMthid2 and ICFlashInvalidate intact. Only FPR, cache
and final startup stop are artificial sc;blr boundaries.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_hardware_boundary_v17 import (ORIGINAL_SHA, START, REGS, HARDWARE,
                                         get_text, bl, linked_target, STOP)

PS = 0x80520FB4
HID_READ = 0x804B79DC
HID_WRITE = 0x804B79E4
IC = 0x805223AC
FPR = 0x8051FBB0
CACHE = 0x80522540
LOW_END = HARDWARE + 36


def u32(data, offset):
    return struct.unpack_from('>I', data, offset)[0]


def verify_hid_sources(read_write: bytes, ic: bytes):
    if len(read_write) != 16 or len(ic) != 16:
        raise ValueError('incomplete HID wrapper or cache invalidation instructions')
    if u32(read_write, 4) != 0x4E800020 or u32(read_write, 12) != 0x4E800020:
        raise ValueError('HID read and write must both return through blr')
    if u32(ic, 12) != 0x4E800020:
        raise ValueError('cache invalidation helper must end with blr')
    # Validate SPR instruction encoding rather than publishing owner instruction bytes.
    def spr_number(code):
        return (((code >> 11) & 31) << 5) | ((code >> 16) & 31)
    if not (u32(read_write, 0) >> 26 == 31 and
            (u32(read_write, 0) >> 1) & 1023 == 339 and
            spr_number(u32(read_write, 0)) == 920):
        raise ValueError('unexpected HID2 mfspr')
    if not (u32(read_write, 8) >> 26 == 31 and
            (u32(read_write, 8) >> 1) & 1023 == 467 and
            spr_number(u32(read_write, 8)) == 920):
        raise ValueError('unexpected HID2 mtspr')
    if not (u32(ic, 0) >> 26 == 31 and spr_number(u32(ic, 0)) == 1008 and
            u32(ic, 8) >> 26 == 31 and spr_number(u32(ic, 8)) == 1008):
        raise ValueError('unexpected HID0 mfspr/mtspr')


def make(owner: Path | None) -> bytes:
    if owner is not None:
        original = owner.read_bytes()
        if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
            raise ValueError('original owner Wii DOL SHA-256 mismatch')
        entry = get_text(original, START, 8)
        registers = get_text(original, REGS, 144)
        hardware = get_text(original, HARDWARE, 36)
        ps = get_text(original, PS, 84)
        hid = get_text(original, HID_READ, 16)
        ic = get_text(original, IC, 16)
    else:
        entry = bl(START, REGS) + bl(START + 4, HARDWARE)
        # Independent synthetic register init, stack must be valid for stwu.
        registers = struct.pack('>III', 0x3860002A, 0x3C208006, 0x4E800020)
        hardware = struct.pack('>4I', 0x7CE000A6, 0x60E72000, 0x7CE00124, 0x7FE802A6)
        hardware += bl(HARDWARE + 16, PS) + bl(HARDWARE + 20, FPR) + bl(HARDWARE + 24, CACHE)
        hardware += struct.pack('>II', 0x7FE803A6, 0x4E800020)
        # Completely synthetic but structurally faithful PPC wrappers and PS initializer.
        # Using the actual owner routine for PS in synthetic mode would publish game code.
        # Instead, synthetic mode exercises exact known PowerPC instruction *semantics*
        # via independently assembled 32-bit opcodes for a different routine.
        ps = b''
        # stack frame and saved return LR
        ps += struct.pack('>III', 0x9421FFE0, 0x7D8802A6, 0x91810024)
        ps += bl(PS + len(ps), HID_READ)
        ps += struct.pack('>I', 0x6463A000)  # oris r3,r3,0xa000
        ps += bl(PS + len(ps), HID_WRITE)
        ps += bl(PS + len(ps), IC)
        ps += struct.pack('>II', 0x7C0004AC, 0x38600000)  # sync; li r3,0
        # GQR0..7 = 0; synthesize mtspr with exact PowerPC bitfield layout.
        for spr in range(912, 920):
            encoded = 31 << 26 | 3 << 21 | (spr & 31) << 16 | ((spr >> 5) & 31) << 11 | 467 << 1
            ps += struct.pack('>I', encoded)
        ps += struct.pack('>4I', 0x81810024, 0x7D8803A6, 0x38210020, 0x4E800020)
        # Construct independent synthetic HID2 and HID0 wrapper instructions.
        def mspr(dest_or_src, spr, ext):
            return (31 << 26) | (dest_or_src << 21) | ((spr & 31) << 16) | (((spr >> 5) & 31) << 11) | (ext << 1)
        hid = struct.pack('>4I', mspr(3,920,339),0x4E800020,mspr(3,920,467),0x4E800020)
        ic = struct.pack('>4I', mspr(4,1008,339),0x60840800,mspr(4,1008,467),0x4E800020)

    if len(hardware) != 36 or len(ps) != 84:
        raise ValueError('hardware or PSInit body has unexpected length')
    for index, target in enumerate((REGS, HARDWARE)):
        if linked_target(u32(entry, index * 4), START + index * 4) != target:
            raise ValueError('first two startup calls changed')
    for index, target in enumerate((PS, FPR, CACHE)):
        if linked_target(u32(hardware, 16 + index * 4), HARDWARE + 16 + index * 4) != target:
            raise ValueError('hardware service call target changed')
    for offset, target in ((12, HID_READ), (20, HID_WRITE), (24, IC)):
        if linked_target(u32(ps, offset), PS + offset) != target:
            raise ValueError('PSInit guest call target changed')
    if u32(hardware, 32) != 0x4E800020 or u32(ps, 80) != 0x4E800020:
        raise ValueError('original hardware or PSInit missing final blr')
    verify_hid_sources(hid, ic)

    # Use ONE low text section for entry/regs/hardware because DOL text
    # section table has at most 7 entries and the nine-function test needs 6.
    low = bytearray(struct.pack('>I', 0x60000000) * ((LOW_END - START) // 4))
    for addr, data in ((START, entry + STOP), (REGS, registers), (HARDWARE, hardware)):
        low[addr - START:addr - START + len(data)] = data
    sections = [(START, bytes(low)), (PS, ps), (HID_READ, hid), (IC, ic),
                (FPR, STOP), (CACHE, STOP)]
    size = 256 + sum((len(data) + 3) & ~3 for _, data in sections)
    output = bytearray(size)
    file_at = 256
    for i, (pc, data) in enumerate(sections):
        for base, value in ((0x00, file_at), (0x48, pc), (0x90, len(data))):
            struct.pack_into('>I', output, base + 4 * i, value)
        output[file_at:file_at + len(data)] = data
        file_at += (len(data) + 3) & ~3
    struct.pack_into('>I', output, 0xe0, START)
    return bytes(output)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('destination', type=Path)
    ap.add_argument('--owner-dol', type=Path)
    args = ap.parse_args()
    if args.destination.exists():
        ap.error('refusing to overwrite existing output')
    b = make(args.owner_dol)
    args.destination.write_bytes(b)
    print(f'V18 verified six-section DOL with real PPC PSInit and HID helpers: {len(b)} bytes; original={bool(args.owner_dol)}')
