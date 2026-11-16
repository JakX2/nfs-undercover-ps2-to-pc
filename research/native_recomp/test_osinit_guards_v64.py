#!/usr/bin/env python3
"""V64 strict owner-image/callgraph mutation and output-safety regression."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_cache_return_v64 import make,ERROR,ERROR_END,CACHE_TAIL,CACHE_END,OSINIT_STOP,FPSCR_READ,FPSCR_WRITE

def read32(buf,off):return struct.unpack_from('>I',buf,off)[0]

def mutate_word(private,pc):
    new=bytearray(private)
    for index in range(7):
        offset=read32(new,4*index)
        base=read32(new,0x48+4*index)
        length=read32(new,0x90+4*index)
        if offset>=0x100 and base<=pc and pc+4<=base+length:
            new[offset+pc-base+3]^=1
            return bytes(new)
    raise ValueError(f'V64 mutation outside private executable text: {pc:#x}')

def rejected(generator,private,filename,folder):
    input_file=folder/(filename+'.dol');output=folder/(filename+'_output')
    input_file.write_bytes(private);output.mkdir()
    try:
        result=subprocess.run((str(generator),str(input_file),str(output)),capture_output=True,text=True,timeout=12)
        if result.returncode==0 or any(output.iterdir()):
            raise AssertionError(f'V64 accepted mutated image or emitted output: {filename}')
    finally:
        input_file.unlink(missing_ok=True)
        for p in output.iterdir():p.unlink()
        output.rmdir()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('owner_original_wii_dol',type=Path)
    p.add_argument('native_generator',type=Path)
    a=p.parse_args()
    image=make(a.owner_original_wii_dol)
    checks=0
    with tempfile.TemporaryDirectory(prefix='v64_error_bridge_guards_') as tmp:
        root=Path(tmp)
        segments=((CACHE_TAIL,CACHE_END),(ERROR,ERROR_END),
                  (FPSCR_READ,FPSCR_WRITE+0x28),(OSINIT_STOP,OSINIT_STOP+8))
        for lo,hi in segments:
            for pc in range(lo,hi,4):
                rejected(a.native_generator,mutate_word(image,pc),f'original_word_{pc:08x}',root)
                checks+=1
        for name,offset,value in (
            ('wrong_entry',0xe0,0x80520674),
            ('text0_offset',0,0x101),('text0_base',0x48,0x80520674),('text0_size',0x90,0x34cc),
            ('text1_offset',4,0x35d4),('text1_base',0x4c,0x805265b0),('text1_size',0x94,0x48e8),
            ('msr_offset',0x10,0x8074),('msr_base',0x58,0x804b7914),('msr_size',0xa0,0x16c),
            ('other_text_offset',0x14,0x81e4),('unexpected_text_slot',0x18,0x210),
            ('data_offset',0x1c,0x8204),('data_length',0xac,0x94),
        ):
            corrupt=bytearray(image)
            struct.pack_into('>I',corrupt,offset,value)
            rejected(a.native_generator,bytes(corrupt),name,root);checks+=1
        rejected(a.native_generator,image[:-4],'truncated_private',root);checks+=1
        rejected(a.native_generator,image+b'FORBIDDEN','trailing_bytes',root);checks+=1
        mutant=bytearray(a.owner_original_wii_dol.read_bytes());mutant[-1]^=1
        changed=root/'modified_original.dol';changed.write_bytes(mutant)
        try:make(changed)
        except ValueError:checks+=1
        else:raise AssertionError('V64 builder accepted changed original-owner SHA-256')
        previous=root/'existing.dol';previous.write_bytes(b'PRESERVE')
        proc=subprocess.run(('python3',str(Path(__file__).with_name('make_osinit_cache_return_v64.py')),
                            str(a.owner_original_wii_dol),str(previous)),capture_output=True,text=True,timeout=30)
        if proc.returncode==0 or previous.read_bytes()!=b'PRESERVE':
            raise AssertionError('V64 builder overwrote existing destination')
        checks+=1
        nonempty=root/'not_empty';nonempty.mkdir();(nonempty/'preserve').write_bytes(b'KEEP')
        valid=root/'valid_original_private.dol';valid.write_bytes(image)
        proc=subprocess.run((str(a.native_generator),str(valid),str(nonempty)),capture_output=True,text=True,timeout=30)
        if proc.returncode==0 or (nonempty/'preserve').read_bytes()!=b'KEEP':
            raise AssertionError('V64 generator overwrote populated directory')
        checks+=1
    print(f'PASS: V64 {checks}/{checks} original PPC/SHA/image-geometry/output-safety guards')

if __name__=='__main__':main()
