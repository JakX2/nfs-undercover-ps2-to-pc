#!/usr/bin/env python3
"""Fail-closed tests for SHA-pinned privately generated original Wii alarm slices.

Exercises DOL layout, PPC source integrity, ownership digest and generator
output safety. Never publishes the original instruction bytes or private DOL.
"""
import argparse
import subprocess
import struct
import tempfile
from pathlib import Path
from make_alarm_v47 import ALARM, SHA, make, be32


def main():
    p = argparse.ArgumentParser()
    p.add_argument('owner_dol', type=Path)
    p.add_argument('generator', type=Path)
    args = p.parse_args()
    original = args.owner_dol.read_bytes()
    blob = make(args.owner_dol)
    count = 0
    with tempfile.TemporaryDirectory(prefix='alarm-v47-negative-') as folder:
        root = Path(folder)
        image = root / 'private_test.dol'
        out = root / 'out'

        def run(data, success=False):
            nonlocal count
            image.write_bytes(data)
            out.mkdir(exist_ok=True)
            proc = subprocess.run([str(args.generator), str(image), str(out)],
                                  capture_output=True, text=True, timeout=15)
            if success:
                assert proc.returncode == 0 and (out / 'output.cpp').is_file(), proc.stderr[-400:]
                (out / 'output.cpp').unlink()
            else:
                assert proc.returncode != 0, 'unsafe mutated private slice was accepted'
                assert not list(out.iterdir()), 'bad private DOL generated output'
            count += 1

        run(blob, success=True)
        # Every word in all genuine original function bodies must be checked.
        for idx in range(3):
            offset, length = be32(blob, 4*idx), be32(blob, 0x90+4*idx)
            for pos in range(offset, offset+length, 4):
                altered = bytearray(blob)
                altered[pos+3] ^= 0x01
                run(altered)
        # All header fields for four test segments are fail-closed.
        for idx in range(4):
            for header in (0, 0x48, 0x90):
                altered = bytearray(blob)
                pos = header+idx*4
                struct.pack_into('>I', altered, pos, be32(altered, pos) ^ 1)
                run(altered)
        for pos in (0xe0, 0xe3):
            altered = bytearray(blob)
            altered[pos] ^= 1
            run(altered)
        run(blob[:-1])
        run(blob + b"\x00")
        # Synthetic stop instruction cannot be altered either.
        stop_at = be32(blob, 3*4)
        for j in range(2):
            altered = bytearray(blob)
            altered[stop_at+j*4+3] ^= 1
            run(altered)
        assert ALARM == be32(blob, 0xe0)
        # A nonempty C++ output path must never be touched.
        marker = out / 'unrelated.txt'
        marker.write_text('preserve unrelated user output', encoding='utf-8')
        image.write_bytes(blob)
        result = subprocess.run([str(args.generator), str(image), str(out)],
                                capture_output=True, text=True, timeout=15)
        assert result.returncode != 0 and marker.read_text() == 'preserve unrelated user output'
        assert [x.name for x in out.iterdir()] == ['unrelated.txt']
        count += 1
        marker.unlink()
        result = subprocess.run([str(args.generator), str(image), str(root/'missing')],
                                capture_output=True, text=True, timeout=15)
        assert result.returncode != 0 and not (root/'missing').exists()
        count += 1
        # Reject owner binary mutation before extracting or writing private code.
        modified = bytearray(original)
        modified[-1] ^= 1
        invalid_owner = root/'wrong_owner.dol'
        invalid_owner.write_bytes(modified)
        try:
            make(invalid_owner)
        except ValueError:
            count += 1
        else:
            raise AssertionError('owner SHA check did not reject unrelated DOL')
        assert SHA == '16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
    print(f'PASS: V47 owner-DOL, original PPC mutation, and output guard {count}/{count} checks')

if __name__ == '__main__':
    main()
