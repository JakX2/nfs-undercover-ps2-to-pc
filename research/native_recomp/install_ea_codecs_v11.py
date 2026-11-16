#!/usr/bin/env python3
"""Install tested, source-only EA HUFF and JDLZ dispatcher headers.

Run V10's installer first for its JDLZ header. This does not patch guest DVD
reads or replace original PowerPC decompression calls automatically.
"""
import argparse
from pathlib import Path

FILES = ('huff_decoder_v11.h', 'ea_resource_decoder_v11.h')


def install(upstream: Path, source_dir: Path):
    destination = upstream / 'nWiiRuntime/include/runtime'
    if not destination.is_dir():
        raise ValueError('NWiiRuntime/include/runtime folder is missing')
    if not (destination / 'jdlz_decoder_v10.h').is_file():
        raise ValueError('install V10 JDLZ header first')
    changes = []
    for name in FILES:
        data = (source_dir / name).read_bytes()
        if not data.startswith(b'#pragma once\n'):
            raise ValueError(f'unexpected header file: {name}')
        target = destination / name
        if target.exists() and target.read_bytes() != data:
            raise ValueError(f'existing header differs: {name}')
        if not target.exists():
            changes.append((target, data))
    for target, data in changes:
        target.write_bytes(data)
    return len(changes)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('nwiirecomp_root', type=Path)
    parser.add_argument('--sources', type=Path, default=Path(__file__).parent)
    args = parser.parse_args()
    print('Installed V11 headers:', install(args.nwiirecomp_root, args.sources))
