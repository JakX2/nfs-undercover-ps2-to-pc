#!/usr/bin/env python3
"""Fail-closed original PPC, DOL geometry, owner image and output safety guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_errorhandler_v63 import make, ORIGINAL_SHA, ERROR, ERROR_END

BASES=(0x805230B8,0x805265AC,0x804B7910)
SIZES=(0x290,0x4c,0xcc)

def rejects(generator,private,name,folder):
    image=folder/(name+'.dol')
    image.write_bytes(private)
    output=folder/(name+'.out')
    output.mkdir()
    # The output MUST be empty here, otherwise an unsafe input might be
    # rejected only for the unrelated pre-populated output directory.
    p=subprocess.run((str(generator),str(image),str(output)),capture_output=True,text=True,timeout=12)
    if p.returncode==0 or any(output.iterdir()):
        raise AssertionError(f'V63 accepted mutated source or wrote unverified output: {name}')
    image.unlink();output.rmdir()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('owner_original_wii_dol',type=Path)
    p.add_argument('generator',type=Path)
    args=p.parse_args()
    original=bytearray(make(args.owner_original_wii_dol))
    n=0
    with tempfile.TemporaryDirectory(prefix='v63_errorhandler_guards_') as td:
        root=Path(td)
        for section,(base,length) in enumerate(zip(BASES,SIZES)):
            off=struct.unpack_from('>I',original,4*section)[0]
            for index in range(0,length,4):
                if section==0 and index>=ERROR_END-ERROR:continue # synthetic stop checked separately
                temp=bytearray(original)
                temp[off+index+3]^=1
                rejects(args.generator,temp,f'instruction_{base+index:08x}',root)
                n+=1
        for section in range(3):
            off=struct.unpack_from('>I',original,4*section)[0]
            for index in range(2):
                temp=bytearray(original)
                temp[off+SIZES[section]-1-index]^=0x01
                rejects(args.generator,temp,f'section_tail_{section}_{index}',root);n+=1
        for name,off,value in (
            ('entry',0xe0,0x805230bc),
            ('code_offset',0,0x104),('code_addr',0x48,0x805230bc),('code_size',0x90,0x28c),
            ('helper_offset',4,0x394),('helper_addr',0x4c,0x805265b0),('helper_size',0x94,0x48),
            ('msr_offset',8,0x3e0),('msr_addr',0x50,0x804b7914),('msr_size',0x98,0xc8),
            ('extra_code',12,0x410),('extra_data',0x1c,0x410),
        ):
            temp=bytearray(original)
            struct.pack_into('>I',temp,off,value)
            rejects(args.generator,temp,name,root);n+=1
        rejects(args.generator,original[:-1],'truncated',root);n+=1
        rejects(args.generator,original+b'EXTRA','trailing_bytes',root);n+=1
        # Check a valid private image cannot be written to a populated directory.
        with tempfile.TemporaryDirectory(dir=root) as d:
            directory=Path(d);marker=directory/'preserve';marker.write_bytes(b'PRESERVE')
            image=root/'valid.dol';image.write_bytes(original)
            p=subprocess.run((str(args.generator),str(image),str(directory)),capture_output=True,text=True,timeout=12)
            if p.returncode==0 or marker.read_bytes()!=b'PRESERVE':raise AssertionError('V63 overwrote protected output')
            n+=1
        src=bytearray(args.owner_original_wii_dol.read_bytes());src[-1]^=1
        image=root/'mutated_original.dol';image.write_bytes(src)
        try:make(image)
        except ValueError:n+=1
        else:raise AssertionError('V63 accepted mutated owner image')
        destination=root/'existing_private.dol';destination.write_bytes(b'PRESERVE')
        result=subprocess.run(('python3',str(Path(__file__).with_name('make_errorhandler_v63.py')),str(args.owner_original_wii_dol),str(destination)),capture_output=True,text=True,timeout=15)
        if result.returncode==0 or destination.read_bytes()!=b'PRESERVE':raise AssertionError('V63 builder overwrote protected output')
        n+=1
    print(f'PASS: V63 {n}/{n} original PPC/mutation/DOL/owner SHA/output safety checks')

if __name__=='__main__':main()
