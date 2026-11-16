#!/usr/bin/env python3
"""Guard tests for original-free NWiiRecomp leaf extraction driver."""
import struct
import subprocess
import sys
from pathlib import Path


def must_fail(binary, dol, start, length, symbol, output):
    proc = subprocess.run([binary, str(dol), start, str(length), symbol,
                           str(output)], capture_output=True, text=True, timeout=10)
    assert proc.returncode != 0, (proc.stdout, proc.stderr)
    assert not output.exists(), 'driver wrote code for rejected function'


def main():
    exe, dol, work = sys.argv[1:4]
    dol, work = Path(dol), Path(work)
    must_fail(exe, dol, '80004000', 4, 'bad', work / 'bad_span.cpp')
    must_fail(exe, dol, '80004001', 8, 'bad', work / 'bad_alignment.cpp')
    must_fail(exe, dol, '80005000', 8, 'bad', work / 'bad_address.cpp')
    must_fail(exe, dol, '80004000', 100, 'bad', work / 'bad_length.cpp')
    must_fail(exe, dol, '80004000', 8, '1invalid', work / 'bad_name.cpp')
    must_fail(exe, dol, '80004000', 8, 'evil;touch', work / 'bad_symbol.cpp')
    data = bytearray(dol.read_bytes())
    struct.pack_into('>I', data, 0x100, 0x48000080)  # branch outside slice
    escaped = work / 'external_branch.dol'
    escaped.write_bytes(data)
    must_fail(exe, escaped, '80004000', 8, 'bad', work / 'bad_branch.cpp')
    struct.pack_into('>I', data, 0x100, 0x48000005)  # branch with link
    linked = work / 'linked_branch.dol'
    linked.write_bytes(data)
    must_fail(exe, linked, '80004000', 8, 'bad', work / 'bad_call.cpp')
    print('PASS: 8 original-free leaf-driver rejection checks')


if __name__ == '__main__':
    main()
