#!/usr/bin/env python3
"""V38 owner-private original Wii OSInit IPC-buffer continuation.

All original PowerPC instructions are read only from a SHA-checked owner DOL.
The repository only receives this independently authored constructor and tests.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_mem2_v37 import make as make_v37, STOP as PREV_STOP
from make_osinit_execparams_v28 import text_at, target, SC, BLR
from make_osinit_hid4_v30 import OSINIT, be32

STOP = 0x805208A8
IPC = 0x8052AE80
TIMEBASE_SECTION = 0x8052A824
NOP = 0x60000000


def validate_ipc(code):
    if len(code) != 24 or be32(code, 20) != BLR:
        raise ValueError('original IPC initialization function size/return changed')
    w = [be32(code, i * 4) for i in range(6)]
    if not (w[0] >> 26 == 15 and (w[0] >> 21) & 31 == 3 and
            w[0] & 0xffff == 0x8000):
        raise ValueError('expected low-memory base in original IPC initialization')
    for index, expected_op, target_reg, base_reg, disp in (
        (1, 32, 0, 3, 0x3130), (2, 36, 0, 13, -16336),
        (3, 32, 0, 3, 0x3134), (4, 36, 0, 13, -3352),
    ):
        ins = w[index]
        if (ins >> 26 != expected_op or (ins >> 21) & 31 != target_reg or
                (ins >> 16) & 31 != base_reg or
                (ins & 0xffff) != (disp & 0xffff)):
            raise ValueError('original IPC helper guest load/store changed')


def make(owner):
    prior = make_v37(owner)  # validates pinned original SHA and all previous code
    original = Path(owner).read_bytes()
    call = text_at(original, PREV_STOP, STOP - PREV_STOP)
    if len(call) != 4 or target(be32(call, 0), PREV_STOP, True) != IPC:
        raise ValueError('original OSInit IPC buffer call target changed')
    ipc = text_at(original, IPC, 24)
    validate_ipc(ipc)
    sections = []
    for i in range(7):
        offset, address, size = (be32(prior, base + i * 4) for base in (0, 0x48, 0x90))
        if offset < 256 or not size or offset + size > len(prior):
            raise ValueError('V37 section geometry invalid')
        sections.append((address, bytearray(prior[offset:offset + size])))
    base, os_text = sections[0]
    if base != OSINIT or be32(os_text, PREV_STOP - OSINIT) != SC:
        raise ValueError('V37 OSInit stop not where expected')
    os_text[PREV_STOP - OSINIT:STOP - OSINIT] = call
    struct.pack_into('>II', os_text, STOP - OSINIT, SC, BLR)
    sections[0] = (base, os_text)
    base, time_text = sections[1]
    if base != TIMEBASE_SECTION or base + len(time_text) > IPC:
        raise ValueError('unexpected private timebase section geometry')
    gap = IPC - (base + len(time_text))
    if gap & 3 or gap > 64 * 1024:
        raise ValueError('unsafe original IPC helper placement')
    time_text.extend(struct.pack('>I', NOP) * (gap // 4))
    time_text.extend(ipc)
    sections[1] = (base, time_text)
    result = bytearray(256 + sum((len(data) + 3) & ~3 for _, data in sections))
    pos = 256
    for i, (address, data) in enumerate(sections):
        for header, value in ((0, pos), (0x48, address), (0x90, len(data))):
            struct.pack_into('>I', result, header + 4 * i, value)
        result[pos:pos + len(data)] = data
        pos += (len(data) + 3) & ~3
    struct.pack_into('>I', result, 0xe0, OSINIT)
    return bytes(result)


if __name__ == '__main__':
    cli = argparse.ArgumentParser()
    cli.add_argument('owner_dol', type=Path)
    cli.add_argument('destination', type=Path)
    args = cli.parse_args()
    if args.destination.exists():
        cli.error('refusing to overwrite existing private output')
    payload = make(args.owner_dol)
    args.destination.write_bytes(payload)
    print('PASS: V38 original Wii IPC initialization private DOL:', len(payload), 'bytes')
