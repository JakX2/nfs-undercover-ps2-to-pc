#!/usr/bin/env python3
"""Fail-closed mutation/output guard for the original EXIInit owner-private fixture."""
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse, subprocess,sys,struct,shutil
from make_exi_poll_v65 import make,ORIGINAL_SHA,ENTRY,STOP
import hashlib

def verify(owner:Path,generator:Path)->None:
    if hashlib.sha256(owner.read_bytes()).hexdigest()!=ORIGINAL_SHA:
        raise RuntimeError('owner-original checksum changed')
    original=make(owner)
    passed=0
    with TemporaryDirectory(prefix='v65_guards_') as d:
        root=Path(d);out=root/'out';out.mkdir()
        def run(blob,expected_fail=True):
            nonlocal passed
            inp=root/'private.dol';inp.write_bytes(blob)
            result=subprocess.run([str(generator),str(inp),str(out)],capture_output=True,text=True)
            if expected_fail and result.returncode==0:
                raise RuntimeError('malformed fixture unexpectedly passed: '+result.stdout)
            if not expected_fail and result.returncode:
                raise RuntimeError('known good fixture was rejected: '+result.stderr)
            if expected_fail and list(out.iterdir()):
                raise RuntimeError('generator wrote output despite rejected test image')
            passed+=1
        run(original,False)
        shutil.rmtree(out);out.mkdir()
        # For each instruction including synthetic explicit stop and BLR, mutate
        # all four byte lanes independently; ensure the hash/recompiler refuses.
        for offset in range(0x100,len(original)):
            b=bytearray(original);b[offset]^=0x01;run(b)
        # Malformed header segment addresses, lengths, offsets, and entry point.
        for position in (0,3,0x48,0x49,0x4b,0x90,0x93,0xe0,0xe3,4,0x1c,0x64,0xac,0x1c+4):
            b=bytearray(original);b[position]^=0x01;run(b)
        run(original[:-1]);run(original+b'\x00')
        # Output guard must reject existent data, without modifying it.
        sentinel=out/'CANARY.txt';sentinel.write_text('keep-me')
        inp=root/'private.dol';inp.write_bytes(original)
        r=subprocess.run([str(generator),str(inp),str(out)],capture_output=True,text=True)
        if r.returncode==0 or sentinel.read_text()!='keep-me':
            raise RuntimeError('output overwrite guard failed')
        passed+=1
        sentinel.unlink()
        invalid=root/'owner-not-original.dol'
        invalid.write_bytes(owner.read_bytes()+b'\x00')
        from make_exi_poll_v65 import make as make_fixture
        try:make_fixture(invalid)
        except ValueError:passed+=1
        else:raise RuntimeError('appended owner DOL accepted')
    print(f'PASS: V65 {passed}/{passed} owner-image, every-byte PPC, private DOL and no-overwrite safety checks')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('original_wii_dol',type=Path)
    parser.add_argument('native_generator',type=Path)
    args=parser.parse_args();verify(args.original_wii_dol,args.native_generator)
