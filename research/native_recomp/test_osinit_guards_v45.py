#!/usr/bin/env python3
"""Fail-closed mutation checks for original-free V45 private DOL pipeline."""
import argparse
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_systemcall_v45 import make, SOURCE, COPY, FLUSH, INVALIDATE, STOP


def be32(blob, at):
    return struct.unpack_from('>I', blob, at)[0]


def run_reject(generator, data, case, home):
    test_file = home / (case + '.dol')
    test_file.write_bytes(data)
    output = home / 'generated'
    output.mkdir(exist_ok=True)
    assert not list(output.iterdir())
    result = subprocess.run([str(generator), str(test_file), str(output)],
                            text=True, capture_output=True, timeout=30)
    assert result.returncode != 0, f'{case}: mutant unexpectedly compiled'
    assert not list(output.iterdir()), f'{case}: generator wrote output on rejection'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('owner_dol', type=Path)
    ap.add_argument('generator', type=Path)
    args = ap.parse_args()
    assert args.generator.is_file()
    baseline = make(args.owner_dol)
    checks = 0
    with tempfile.TemporaryDirectory(prefix='v45_owner_guard_') as scratch:
        home = Path(scratch)
        modified_owner = bytearray(args.owner_dol.read_bytes())
        modified_owner[-1] ^= 0x01
        dirty_owner = home / 'sha_mismatch.dol'
        dirty_owner.write_bytes(modified_owner)
        try:
            make(dirty_owner)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('owner SHA guard did not reject mutated game DOL')
        # Check every private source/template and helper instruction, including
        # the source-end NOP and the synthetic syscall/blr termination.
        regions = ((0, SOURCE, 128), (1, COPY, 80), (2, FLUSH, 44),
                   (3, INVALIDATE, 52), (4, STOP, 8))
        for section, guest, length in regions:
            offset = be32(baseline, 4 * section)
            assert be32(baseline, 0x48 + 4 * section) == guest
            assert be32(baseline, 0x90 + 4 * section) == length
            for word in range(length // 4):
                mutant = bytearray(baseline)
                addr = offset + word * 4
                struct.pack_into('>I', mutant, addr,
                                 be32(mutant, addr) ^ (1 << (word % 31)))
                run_reject(args.generator, mutant, f'section{section}_word{word}', home)
                checks += 1
        # DOL geometry and entry-point mutations must be rejected *before*
        # generating anything. These use source-only metadata modifications.
        edits = (
            ('entry', 0xE0, 0x8000403C),
            ('text_offset', 0x00, 0),
            ('text_length', 0x90, 0),
            ('text_address', 0x48, SOURCE + 4),
            ('copy_address', 0x4C, COPY + 4),
            ('text_overlap', 0x04, be32(baseline, 0x00)),
            ('extra_text', 0x14, 0x120),
            ('extra_data', 0x1C, 0x120),
            ('bad_cache_size', 0x98, 40),
            ('bad_source_size', 0x90, 124),
            ('changed_stop_size', 0xA0, 4),
        )
        for name, offset, value in edits:
            mutant = bytearray(baseline)
            struct.pack_into('>I', mutant, offset, value)
            run_reject(args.generator, mutant, name, home)
            checks += 1
        private = home / 'owner-private.dol'
        private.write_bytes(baseline)
        generated = home / 'must_preserve'
        generated.mkdir()
        sentinel = generated / 'keep.txt'
        sentinel.write_text('do not touch')
        result = subprocess.run([str(args.generator),str(private),str(generated)],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode != 0 and sentinel.read_text() == 'do not touch'
        checks += 1
        dest = home / 'existing.dol'
        dest.write_bytes(b'KEEP_THIS')
        builder = Path(__file__).with_name('make_osinit_systemcall_v45.py')
        result = subprocess.run(['python3', str(builder),str(args.owner_dol),str(dest)],
                                capture_output=True, text=True, timeout=30)
        assert result.returncode != 0 and dest.read_bytes() == b'KEEP_THIS'
        checks += 1
    print(f'PASS: V45 {checks}/{checks} private-DOL corruption/SHA/overwrite guards')


if __name__ == '__main__':
    main()
