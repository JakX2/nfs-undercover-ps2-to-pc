#!/usr/bin/env python3
"""Fail-closed checks for SHA-pinned private SetInterruptMask fixture/generator."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from make_setmask_v54 import make, ENTRY, STOP


def verify(owner: Path, generator: Path):
    original = owner.read_bytes()
    valid = make(owner)
    count = 0
    with tempfile.TemporaryDirectory(prefix='v54_setmask_guards_') as temp:
        work = Path(temp)
        source = work / 'source.dol'
        outdir = work / 'out'
        outdir.mkdir()

        def reject(data: bytes, case: str):
            nonlocal count
            source.write_bytes(data)
            process = subprocess.run([str(generator), str(source), str(outdir)],
                                     capture_output=True, text=True, timeout=10)
            if process.returncode == 0 or any(outdir.iterdir()):
                raise AssertionError(f'fail-closed generator accepted invalid {case}')
            count += 1

        # Every instruction in the original 0x25c-byte function and both synthetic
        # terminal words must be pinned; this also detects mutated branch targets.
        for offset in range(0x100, 0x100 + 0x264, 4):
            mutated = bytearray(valid)
            mutated[offset + (offset // 4) % 4] ^= 0x01
            reject(mutated, f'guest PPC instruction offset {offset:#x}')

        # All 18 DOL segment descriptors (7 text, 11 data), including unused slots.
        for base, total in ((0x00, 7), (0x48, 7), (0x90, 7),
                            (0x1c, 11), (0x64, 11), (0xac, 11)):
            for i in range(total):
                mutated = bytearray(valid)
                mutated[base + i*4 + 3] ^= 1
                reject(mutated, f'private DOL descriptor {base:#x}:{i}')
        mutated = bytearray(valid)
        mutated[0xe3] ^= 1
        reject(mutated, 'private entrypoint')
        reject(valid[:-1], 'truncated private DOL')
        reject(valid + b'EXTRA', 'appended bytes to private DOL')

        original_path = work / 'owner.dol'
        for case, data in [('owner SHA mutation', bytes([original[0] ^ 1]) + original[1:]),
                           ('appended owner image', original + b'EXTRA')]:
            original_path.write_bytes(data)
            try:
                make(original_path)
            except ValueError:
                count += 1
            else:
                raise AssertionError('accepted '+case)

        existing = work / 'existing.dol'
        existing.write_bytes(b'CANARY')
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('make_setmask_v54.py')),
                                  str(owner), str(existing)],capture_output=True,text=True,timeout=10)
        if process.returncode == 0 or existing.read_bytes() != b'CANARY':
            raise AssertionError('private-output overwrite guard failed')
        count += 1

        source.write_bytes(valid)
        sentinel = outdir / 'canary.txt'
        sentinel.write_bytes(b'CANARY')
        result = subprocess.run([str(generator), str(source), str(outdir)],
                                capture_output=True, text=True,timeout=10)
        if result.returncode == 0 or sentinel.read_bytes()!=b'CANARY':
            raise AssertionError('generator overwrote nonempty output directory')
        count += 1
    print(f'PASS: {count}/{count} V54 original PPC, SHA, DOL bounds and safe-output guards')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('owner_dol',type=Path)
    p.add_argument('native_generator',type=Path)
    a=p.parse_args()
    verify(a.owner_dol, a.native_generator)
