#!/usr/bin/env python3
"""Original-free rejection tests for a source-grounded PPC BL slice extractor."""
import struct
import subprocess
import sys
from pathlib import Path


def run(binary, dol, output_dir, *spans, should_pass=False):
    before = sorted(p.name for p in output_dir.iterdir())
    p = subprocess.run([str(binary), str(dol), str(output_dir), *spans],
                       capture_output=True, text=True, timeout=20)
    if should_pass:
        assert p.returncode == 0, (p.stdout, p.stderr)
    else:
        assert p.returncode != 0, (spans, p.stdout, p.stderr)
        after = sorted(p.name for p in output_dir.iterdir())
        assert after == before, ('rejected extraction wrote files', spans, after)


def main():
    binary, dol, tmp = map(Path, sys.argv[1:4])
    output_dir = tmp / 'rejections'
    output_dir.mkdir(exist_ok=True)
    parent = '80004000:24'
    child = '80004018:8'
    bad_cases = [
        (parent,),
        (parent, parent),
        ('80004000:20', child),
        ('80004001:24', child),
        ('70004000:24', child),
        ('80004000:4097', child),
        (parent, '80004004:8'),
        (parent, '80004018:4'),
        (parent, '80004020:8'),
        ('80004018:8', '80004020:8'),
        ('not-a-number:24', child),
        ('80004000:24:extra', child),
    ]
    for case in bad_cases:
        run(binary, dol, output_dir, *case)
    original = bytearray(dol.read_bytes())
    for label, opcode in (
        ('external_call', 0x48000021),
        ('unconditional_external_jump', 0x48000020),
        ('syscall', 0x44000002),
        ('branch_to_register', 0x4e800420),
        ('local_link', 0x48000005),
    ):
        changed = bytearray(original)
        struct.pack_into('>I', changed, 0x108, opcode)
        mutant = tmp / (label + '.dol')
        mutant.write_bytes(changed)
        run(binary, mutant, output_dir, parent, child)
    print(f'PASS: {len(bad_cases)+5} original-free unsafe callgraph rejection cases')


if __name__ == '__main__':
    main()
