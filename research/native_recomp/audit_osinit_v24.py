#!/usr/bin/env python3
"""Owner-only original Wii OSInit direct-call audit; never emits PPC bytes.

Reads the user's SHA-verified DOL locally. Prints addresses and counts only,
not instructions, translated source, game assets or binary data.
"""
import argparse
import hashlib
import struct
from collections import Counter
from pathlib import Path
from make_hardware_boundary_v17 import ORIGINAL_SHA, get_text

ENTRY = 0x80520670
LENGTH = 1412


def audit(path: Path):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ORIGINAL_SHA:
        raise ValueError('original Wii DOL SHA-256 mismatch')
    code = get_text(raw, ENTRY, LENGTH)
    calls = []
    for i in range(LENGTH // 4):
        pc = ENTRY + 4*i
        op = struct.unpack_from('>I', code, i*4)[0]
        if op >> 26 != 18 or not (op & 1):
            continue
        delta = op & 0x03FFFFFC
        if delta & 0x02000000:
            delta -= 0x04000000
        target = (delta if op & 2 else pc + delta) & 0xffffffff
        calls.append((pc,target))
    counts = Counter(target for _,target in calls)
    if len(calls)!=59 or len(counts)!=54:
        raise ValueError('OSInit guest direct-call census changed')
    return calls,counts


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('original_wii_dol',type=Path)
    args=parser.parse_args()
    edges,counts=audit(args.original_wii_dol)
    print(f'PASS: OSInit original {LENGTH}-byte body, {len(edges)} direct BL calls, {len(counts)} distinct targets')
    print('First direct-call edges (guest addresses only):')
    for pc,target in edges[:20]:
        print(f'  {pc:08X} -> {target:08X}')
