#!/usr/bin/env python3
"""Original-free negative tests for bounded native startup slice and generator."""
import os
import subprocess
import struct
import sys
from pathlib import Path
from make_startup_boundary_v16 import branch_target, build


def expect_error(args, output=None):
    result = subprocess.run(args, capture_output=True, text=True, timeout=15)
    if result.returncode == 0:
        raise AssertionError('rejected input accepted: ' + str(args))
    if output is not None and any(output.iterdir()):
        raise AssertionError('rejected input caused generated game code to be written')


def main():
    generator, slice_tool, working = sys.argv[1:4]
    work = Path(working)
    fixture = work / 'synthetic_startup.dol'
    source = fixture.read_bytes()
    assert build(None) == source
    checks = 1
    # Compute test branch encodings independently; no owner DOL bytes in fixtures.
    for pc, expected in ((0x8000403C, 0x800041A8),
                         (0x80004040, 0x800042E0)):
        word = 0x48000001 | ((expected - pc) & 0x03FFFFFC)
        assert branch_target(word,pc) == expected
        checks += 1
    for bad_word in (0x48000000,0x48000002,0x44000002,0x4E800020):
        try:
            branch_target(bad_word,0x8000403c)
            raise AssertionError('invalid BL accepted')
        except ValueError:
            checks += 1

    out = work / f'rejected_output_{os.getpid()}'
    out.mkdir(exist_ok=False)
    def corrupt(label, writer):
        nonlocal checks
        data = bytearray(source)
        writer(data)
        tmp = work / (label+'.dol')
        tmp.write_bytes(data)
        expect_error([generator,str(tmp),str(out),'synthetic'],out)
        checks += 1

    corrupt('wrong_first_branch',lambda b: struct.pack_into('>I',b,0x100,0x48000001))
    corrupt('wrong_second_branch',lambda b: struct.pack_into('>I',b,0x104,0x48000001))
    corrupt('missing_stop',lambda b: struct.pack_into('>I',b,0x110,0x60000000))
    corrupt('missing_blr',lambda b: struct.pack_into('>I',b,0x10c,0x60000000))
    corrupt('wrong_entry',lambda b: struct.pack_into('>I',b,0xe0,0x800041a8))
    corrupt('wrong_register_size',lambda b: struct.pack_into('>I',b,0x94,4))
    corrupt('unaligned_text_address',lambda b: struct.pack_into('>I',b,0x4c,0x800041a9))
    corrupt('truncated_text_size',lambda b: struct.pack_into('>I',b,0x90,4096))
    corrupted_stop=bytearray(source)
    struct.pack_into('>I',corrupted_stop,0x114,0x60000000)
    tmp=work/'no_stop_blr.dol'; tmp.write_bytes(corrupted_stop)
    expect_error([generator,str(tmp),str(out),'synthetic'],out);checks+=1
    expect_error([generator,str(fixture),str(out),'owner'],out);checks+=1
    expect_error([generator,str(fixture),str(out),'nonsense'],out);checks+=1
    expect_error([generator,str(work/'no_such.dol'),str(out),'synthetic'],out);checks+=1
    out.joinpath('already_exists').write_text('marker')
    expect_error([generator,str(fixture),str(out),'synthetic']);checks+=1
    before=out.joinpath('already_exists').read_text()
    assert before=='marker';checks+=1
    fake=work/'not_real_owner.dol';fake.write_bytes(source)
    target=work/'not_generated.dol'
    expect_error([sys.executable,slice_tool,str(target),'--owner-dol',str(fake)]);checks+=1
    assert not target.exists();checks+=1
    expect_error([sys.executable,slice_tool,str(fixture)]);checks+=1
    print(f'PASS: {checks} startup generator/input rejection and independent fixture checks')


if __name__ == '__main__':
    main()
