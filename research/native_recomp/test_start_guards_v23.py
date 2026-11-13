#!/usr/bin/env python3
"""Original-free malformed-DOL and private-output regression for V23."""
import argparse
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from make_start_to_data_v23 import make, START, RETURN_PC, DATA_INIT, TABLE, SYNTH_DATA_DEST
from make_hardware_boundary_v17 import ORIGINAL_SHA
from make_initdata_slice_v22 import parse_table, make_synthetic_table


def u32(blob, offset):
    return struct.unpack_from('>I', blob, offset)[0]


def address_offset(blob, address):
    for i in range(7):
        off, base, size=(u32(blob, j + i*4) for j in (0,0x48,0x90))
        if off and base <= address and address+4 <= base+size:
            return off+address-base
    raise ValueError('guest address not mapped')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('generator',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    assert args.generator.is_file()
    synthetic=make(None)
    checks=0
    with tempfile.TemporaryDirectory(prefix='v23_guard_') as path:
        work=Path(path)
        def failed(blob,mode='synthetic'):
            nonlocal checks
            inp=work/'bad.dol'
            dest=work/'generated'
            inp.write_bytes(blob)
            dest.mkdir()
            p=subprocess.run([str(args.generator),str(inp),str(dest),mode],
                             capture_output=True,text=True,timeout=12)
            assert p.returncode!=0,(mode,p.stdout,p.stderr)
            assert not list(dest.iterdir()),'invalid DOL wrote generated source'
            dest.rmdir()
            checks+=1
        def change_word(address,value):
            blob=bytearray(synthetic)
            struct.pack_into('>I',blob,address_offset(blob,address),value)
            failed(bytes(blob))
        for blob in (b'',synthetic[:0xff],synthetic[:-16]):
            failed(blob)
        for offset,value in ((0xe0,0x80000000),(0,0),(0x48,0x80000000),
                             (0x90,0xfffffffc),(0x1c,0),(0xac,0),
                             (0x64,0x90000001)):
            buf=bytearray(synthetic)
            struct.pack_into('>I',buf,offset,value)
            failed(bytes(buf))
        for address,value in (
             (START,0x60000000),(START+4,0x60000000),
             (START+24,0x60000000),(RETURN_PC,0x60000000),
             (RETURN_PC+4,0x60000000),
             (DATA_INIT,0x60000000),(DATA_INIT+12,0x60000000),
             (0x805223bc,0x60000000),(0x804b7930,0x60000000),
                         ):
            change_word(address,value)
        failed(synthetic,mode='owner')
        failed(synthetic,mode='invalid')
        dirty=work/'dirty';dirty.mkdir(); (dirty/'keep.txt').write_text('untouched')
        inp=work/'valid.dol';inp.write_bytes(synthetic)
        p=subprocess.run([str(args.generator),str(inp),str(dirty),'synthetic'],
                         capture_output=True,text=True,timeout=12)
        assert p.returncode!=0 and (dirty/'keep.txt').read_text()=='untouched'
        checks+=1
        p=subprocess.run([str(args.generator),str(inp),str(work/'missing'),'synthetic'],
                         capture_output=True,text=True,timeout=12)
        assert p.returncode!=0 and not (work/'missing').exists()
        checks+=1
        existing=work/'existing.dol';existing.write_bytes(b'preserve')
        p=subprocess.run(['python3',str(Path(__file__).with_name('make_start_to_data_v23.py')),
                          str(existing)],capture_output=True,text=True,timeout=12)
        assert p.returncode!=0 and existing.read_bytes()==b'preserve'
        checks+=1
        wrong=work/'not-original.dol';wrong.write_bytes(synthetic)
        try:make(wrong)
        except ValueError:checks+=1
        else:raise AssertionError('wrong original DOL hash accepted')
        # Parent composition must fail *before* output if its V21 root or its
        # first two BL destinations no longer match source-grounded expectations.
        for header,value in ((0x90,16),(0x48,0x80004100)):
            bad=bytearray(synthetic)
            struct.pack_into('>I',bad,header,value)
            with patch('make_start_to_data_v23.make_v21',return_value=bytes(bad)):
                try:make(None)
                except ValueError:checks+=1
                else:raise AssertionError('changed inherited V21 layout accepted')
        copies,zeros=parse_table(make_synthetic_table())
        assert copies==[(0x80031000,0x80032000,65)] and len(zeros)==2
        checks+=1
        assert u32(synthetic,address_offset(synthetic,RETURN_PC))==0x44000002
        checks+=1
        assert u32(synthetic,address_offset(synthetic,DATA_INIT)+12)==0x4e800020
        checks+=1
        assert SYNTH_DATA_DEST==0x80036000
        checks+=1
        if args.owner_dol:
            owner=args.owner_dol.read_bytes()
            assert hashlib.sha256(owner).hexdigest()==ORIGINAL_SHA
            joined=make(args.owner_dol)
            assert joined!=synthetic and u32(joined,0xe0)==START
            checks+=1
            bad=bytearray(owner);bad[0x100]^=0x01
            badpath=work/'mutated_original.dol';badpath.write_bytes(bad)
            try:make(badpath)
            except ValueError:checks+=1
            else:raise AssertionError('mutated real original DOL accepted')
    print(f'PASS: {checks} V23 source-only malformed-image, SHA and output-safety checks')


if __name__=='__main__':
    main()
