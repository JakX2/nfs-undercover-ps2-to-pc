#!/usr/bin/env python3
"""Report source-grounded first-stage PowerPC startup edges, no game bytes.

Reads a private original DOL with an exact known SHA256, then prints only
program counter relationships and known symbol names. Do not publish DOL data.
"""
import argparse
import hashlib
import struct
from pathlib import Path

from make_startup_boundary_v16 import OWNER_SHA256, extract_text

FUNCTIONS = (
    ('__start', 0x8000403C, 364),
    ('__init_registers', 0x800041A8, 144),
    ('__init_hardware', 0x800042E0, 36),
    ('__init_data', 0x80004238, 168),
)
NAMES = {
    0x80004000: '__check_pad3', 0x80004028: '__set_debug_bba',
    0x80004034: '__get_debug_bba', 0x800041A8: '__init_registers',
    0x80004238: '__init_data', 0x800042E0: '__init_hardware',
    0x80004304: '__flush_cache', 0x80004338: 'memcpy',
    0x8000443C: 'memset', 0x804E5020: 'DBInit',
    0x80520670: 'OSInit', 0x80555F14: 'InitMetroTRK_BBA',
    0x8052DAEC: '__init_user', 0x802D3F40: 'main',
    0x80520FB4: '__OSPSInit', 0x8051FBB0: '__OSFPRInit',
    0x80522540: '__OSCacheInit', 0x8052DB54: 'exit',
}


def direct_link_edges(data: bytes, start: int):
    found = []
    for off in range(0, len(data), 4):
        word = struct.unpack_from('>I', data, off)[0]
        if (word >> 26) != 18 or not (word & 1):
            continue
        displacement = word & 0x03FFFFFC
        if displacement & 0x02000000:
            displacement -= 0x04000000
        target = (displacement if word & 2 else start + off + displacement) & 0xFFFFFFFF
        found.append((start + off, target))
    return found


def audit(path: Path):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != OWNER_SHA256:
        raise ValueError('original owner DOL checksum mismatch')
    edges = {}
    for name, start, size in FUNCTIONS:
        edges[name] = direct_link_edges(extract_text(payload, start, size), start)
    first = edges['__start']
    hardware = edges['__init_hardware']
    init_data = edges['__init_data']
    if len(first) != 11 or [dest for _, dest in first[:3]] != [0x800041A8, 0x800042E0, 0x80004238]:
        raise ValueError('unexpected original startup direct call order')
    if [dest for _, dest in hardware] != [0x80520FB4, 0x8051FBB0, 0x80522540]:
        raise ValueError('unexpected hardware initialization dependencies')
    if [dest for _, dest in init_data] != [0x80004338, 0x80004304, 0x8000443C]:
        raise ValueError('unexpected data initialization helpers')
    if edges['__init_registers']:
        raise ValueError('register initialization unexpectedly calls other routines')
    return edges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('original_owner_dol', type=Path)
    a = parser.parse_args()
    for name, entries in audit(a.original_owner_dol).items():
        print(name + ':')
        if not entries:
            print('  (no direct BL edges)')
        for origin, target in entries:
            print(f'  0x{origin:08X} -> 0x{target:08X}  {NAMES.get(target, "(unlabeled)")}')
    print('BOUNDARY: test stops synthetically at __init_hardware; actual Wii services not executed')


if __name__ == '__main__':
    main()
