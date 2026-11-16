#!/usr/bin/env python3
"""Install original-free JDLZ/HUFF native codec headers into NWiiRuntime.

Does not hook DVD reads or replace original PowerPC decompression calls.
Fail closed on header collisions. Idempotent on byte-identical copies.
"""
import argparse
from pathlib import Path

HEADERS = ('jdlz_decoder_v10.h', 'huff_decoder_v11.h', 'ea_resource_decoder_v11.h')

def install(upstream: Path, toolkit: Path):
    target_dir = upstream / 'nWiiRuntime/include/runtime'
    if not target_dir.is_dir():
        raise ValueError('not an NWiiRecomp runtime source directory')
    # Check everything first, avoid partially installing on a collision.
    writes=[]
    for name in HEADERS:
        source=(toolkit/name).read_bytes()
        if not source.startswith(b'#pragma once\n'):
            raise ValueError(f'invalid header source {name}')
        destination=target_dir/name
        if destination.exists():
            if destination.read_bytes()!=source:
                raise ValueError(f'header collision at {destination}')
        else:
            writes.append((destination,source))
    for path,source in writes:
        path.write_bytes(source)
    return len(writes)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('upstream_root',type=Path)
    p.add_argument('--toolkit',type=Path,default=Path(__file__).parent)
    a=p.parse_args()
    print('installed original-free codec headers:',install(a.upstream_root,a.toolkit))
