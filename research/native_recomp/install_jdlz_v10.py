#!/usr/bin/env python3
"""Safely install original-free JDLZ v02 header into a NWiiRuntime source tree.

This does not intercept guest DVD reads or override the original PowerPC
JLZDecompress. It provides a reusable native implementation for future HLE or
offline resource inspection, without distributing proprietary resources.
"""
import argparse
from pathlib import Path


def install(root: Path, header: Path) -> bool:
    target = root / 'nWiiRuntime/include/runtime/jdlz_decoder_v10.h'
    source = header.read_bytes()
    if not source.startswith(b'#pragma once\n'):
        raise ValueError('unexpected source file, refusing installation')
    if target.exists():
        if target.read_bytes() != source:
            raise ValueError('existing runtime JDLZ header differs, refusing overwrite')
        return False
    if not target.parent.is_dir():
        raise ValueError('no NWiiRuntime header directory')
    target.write_bytes(source)
    return True


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('nwiirecomp_root', type=Path)
    ap.add_argument('--header', type=Path,
                    default=Path(__file__).with_name('jdlz_decoder_v10.h'))
    args = ap.parse_args()
    print('Installed JDLZ header:', install(args.nwiirecomp_root, args.header))
