#!/usr/bin/env python3
"""Owner-private fixture restoring the genuine L2 setup prefix, stopping before polling.

No original Wii opcode bytes are embedded in this independent test-source file.
"""
import argparse
import struct
from pathlib import Path
from make_osinit_l2cr_v60 import make as inherited, L2_DISABLED_STOP, L2_ENABLED_STOP
from make_osinit_cache_l1_v59 import OSINIT, NOP
from make_alarm_v47 import original_text, call_target, be32, SC, BLR

NEW_STOP = 0x805225EC
MFMSR = 0x804B7910
MTMSR = 0x804B7918
READ_L2 = 0x804B7930
WRITE_L2 = 0x804B7938


def make(owner: Path) -> bytes:
    previous = bytearray(inherited(owner))
    original = owner.read_bytes()
    body = original_text(original, L2_DISABLED_STOP, NEW_STOP - L2_DISABLED_STOP)
    if len(body) != 0x4c:
        raise ValueError('L2 setup prefix extent differs')
    expected_calls = {
        0x805225A0: MFMSR,
        0x805225B0: MTMSR,
        0x805225BC: READ_L2,
        0x805225C4: WRITE_L2,
        0x805225D0: READ_L2,
        0x805225D8: WRITE_L2,
        0x805225E0: READ_L2,
        0x805225E8: WRITE_L2,
    }
    for site, callee in expected_calls.items():
        if call_target(body, site, L2_DISABLED_STOP) != callee:
            raise ValueError(f'original L2 cache setup call at {site:#x} changed')
    code_offset, guest_base, code_size = [be32(previous, off) for off in (0, 0x48, 0x90)]
    if (code_offset < 0x100 or guest_base != OSINIT or
        NEW_STOP + 8 > guest_base + code_size or
        code_offset + code_size > len(previous)):
        raise ValueError('V61 test section geometry differs')
    at = code_offset + L2_DISABLED_STOP - guest_base
    if be32(previous, at) != SC or be32(previous, at+4) != BLR or any(
        be32(previous, at+j) != NOP for j in range(8, len(body), 4)
    ):
        raise ValueError('V61 original prefix would overwrite non-synthetic code')
    previous[at:at + len(body)] = body
    # The existing helper segment is full. Extend its file extent backward
    # by inserting 16 owner-original bytes before its old contents, keeping
    # all addresses unchanged and moving only subsequent private file offsets.
    helper_off, helper_base, helper_size = [be32(previous, off) for off in (0x10, 0x58, 0xA0)]
    if (helper_base != 0x804B7920 or helper_size != 0x160 or
        helper_off < 0x100 or helper_off + helper_size > len(previous)):
        raise ValueError('V61 helper section geometry changed')
    msr_helpers = original_text(original, MFMSR, 16)
    if len(msr_helpers) != 16 or be32(msr_helpers, 4) != BLR or be32(msr_helpers, 12) != BLR:
        raise ValueError('V61 original MSR helpers changed')
    previous[helper_off:helper_off] = msr_helpers
    struct.pack_into('>I', previous, 0x58, MFMSR)
    struct.pack_into('>I', previous, 0xA0, helper_size + 16)
    for file_off in (0x14, 0x1c):
        old_off = be32(previous, file_off)
        if old_off < helper_off + helper_size:
            raise ValueError('V61 following DOL sections overlap extended helper')
        struct.pack_into('>I', previous, file_off, old_off + 16)
    stop_at = code_offset + NEW_STOP - guest_base
    if be32(previous, stop_at) != NOP or be32(previous, stop_at + 4) != NOP:
        raise ValueError('V61 L2 polling stop is not synthetic padding')
    struct.pack_into('>II', previous, stop_at, SC, BLR)
    return bytes(previous)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('original_owner_wii_dol', type=Path)
    p.add_argument('new_private_test_dol', type=Path)
    args = p.parse_args()
    if args.new_private_test_dol.exists():
        p.error('refuse to overwrite private original-code test image')
    args.new_private_test_dol.write_bytes(make(args.original_owner_wii_dol))
    print('PASS: V61 authentic original L2CR setup prefix placed privately')
