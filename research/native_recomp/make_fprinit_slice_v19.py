#!/usr/bin/env python3
"""Build original-free synthetic or SHA-pinned owner-private __OSFPRInit DOL.

The full owner's __OSFPRInit is copied ONLY to a private temp file. No game
instructions or constants are embedded in this script or the published ZIP.
"""
import argparse
import hashlib
import struct
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text
from make_psinit_slice_v18 import make as make_v18, FPR

FPR_SIZE = 296  # owner ELF symbol table, 74 PowerPC instructions


def pack(*words):
    return struct.pack('>' + 'I' * len(words), *words)


def synthetic_fpr():
    # Independently authored test FPU initializer, deliberately not the game's
    # sequence: no HID2 conditional, different GPRs and constant addresses.
    words = [0x3c608003, 0x60634000, (56 << 26) | (3 << 16)]
    # One paired-single load followed by ps_mr to each other register.
    words += [(4 << 26) | (i << 21) | (72 << 1) for i in range(1, 32)]
    words += [0x3ca08003, 0x60a54100, (50 << 26) | (5 << 16)]
    # One scalar load followed by fmr to each other register.
    words += [(63 << 26) | (i << 21) | (72 << 1) for i in range(1, 32)]
    words += [(63 << 26) | (0xff << 17) | (711 << 1), 0x4e800020]
    assert len(words) == 70
    return pack(*words)


def validate_original_fpr(body):
    if len(body) != FPR_SIZE:
        raise ValueError('original FPR span incomplete')
    w = list(struct.unpack('>74I', body))
    if w[-1] != 0x4e800020:
        raise ValueError('FPR initializer does not end in blr')
    if [(v >> 26) for v in w].count(4) != 31 or [(v >> 26) for v in w].count(63) != 32:
        raise ValueError('owner FPR paired-single/scalar instruction census mismatch')
    if not (w[8] >> 26 == 56 and w[40] >> 26 == 50 and ((w[72] >> 1) & 1023) == 711):
        raise ValueError('original FPR essential PSQ/LFD/MTFSF forms altered')
    if sum((v >> 1) & 1023 == 72 and v >> 26 == 4 for v in w) != 31:
        raise ValueError('original paired-single copies incomplete')
    if sum((v >> 1) & 1023 == 72 and v >> 26 == 63 for v in w) != 31:
        raise ValueError('original scalar copies incomplete')
    # PSE-enabled path should skip to the scalar LFD with a single local BC.
    branch = w[5]
    if branch >> 26 != 16:
        raise ValueError('original FPR PSE branch absent')
    disp = struct.unpack('>h', struct.pack('>H', branch & 0xfffc))[0]
    if FPR + 20 + disp != FPR + 40 * 4:
        raise ValueError('original FPR PSE branch target changed')


def make(owner: Path | None):
    base = make_v18(owner)
    if owner is not None:
        original = owner.read_bytes()
        if hashlib.sha256(original).hexdigest() != ORIGINAL_SHA:
            raise ValueError('owner DOL SHA mismatch')
        fpr = get_text(original, FPR, FPR_SIZE)
        validate_original_fpr(fpr)
    else:
        fpr = synthetic_fpr()
    sections=[]
    for i in range(6):
        offset, guest, size = (
            struct.unpack_from('>I', base, i * 4)[0],
            struct.unpack_from('>I', base, 0x48 + i * 4)[0],
            struct.unpack_from('>I', base, 0x90 + i * 4)[0],
        )
        if offset == 0 or size == 0:
            raise ValueError('unexpected missing V18 source section')
        payload = fpr if i == 4 else base[offset:offset+size]
        sections.append((guest, payload))
    result = bytearray(256 + sum((len(b)+3)&~3 for _, b in sections))
    file_at=256
    for i,(guest,payload) in enumerate(sections):
        for base_index,value in ((0,file_at),(0x48,guest),(0x90,len(payload))):
            struct.pack_into('>I', result, base_index+4*i, value)
        result[file_at:file_at+len(payload)]=payload
        file_at+=(len(payload)+3)&~3
    struct.pack_into('>I', result, 0xe0, 0x8000403c)
    return bytes(result)


if __name__ == '__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('destination',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    if args.destination.exists():
        ap.error('refusing to overwrite existing generated output')
    b=make(args.owner_dol)
    args.destination.write_bytes(b)
    print('Wrote private V19 DOL slice:',len(b),'bytes; original=',bool(args.owner_dol))
