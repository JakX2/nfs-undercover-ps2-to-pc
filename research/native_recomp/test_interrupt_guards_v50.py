#!/usr/bin/env python3
"""Original-free negative tests for private Wii interrupt+memset fixture."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_interrupt_prefix_v50 import make


def get32(data, where):
    return struct.unpack_from('>I',data,where)[0]


def rejected(generator:Path, dest:Path, data:bytes, name:str):
    file=dest / (name+'.dol')
    file.write_bytes(data)
    out=dest/'generated'
    out.mkdir(exist_ok=True)
    if list(out.iterdir()):raise AssertionError('test output not empty')
    res=subprocess.run([str(generator),str(file),str(out)],capture_output=True,text=True,timeout=30)
    if res.returncode==0 or list(out.iterdir()):
        raise AssertionError(f'unsafe private fixture was accepted: {name}')


def test(original:Path,generator:Path):
    clean=make(original)
    count=0
    with tempfile.TemporaryDirectory(prefix='v50_native_guard_') as d:
        home=Path(d)
        bad=bytearray(original.read_bytes());bad[-1]^=1
        path=home/'modified_original.dol';path.write_bytes(bad)
        try:make(path)
        except ValueError:count+=1
        else:raise AssertionError('modified owner DOL passed original SHA pin')
        for section in range(2):
            o=get32(clean,4*section)
            n=get32(clean,0x90+4*section)
            for at in range(0,n,4):
                mutated=bytearray(clean)
                where=o+at
                struct.pack_into('>I',mutated,where,get32(mutated,where)^1)
                rejected(generator,home,mutated,f'ppc_{section}_{at:03x}')
                count+=1
        metadata=(('entry',0xe0,0x8000403c),
                  ('sec0_len',0x90,0x30),('sec1_len',0x94,0xe0),
                  ('sec0_addr',0x48,0x80526620),('sec1_addr',0x4c,0x8000438c),
                  ('sec0_off',0,0),('sec1_off',4,0x100),
                  ('third_text',8,0x100),('extra_data',0x1c,0x200),
                  ('extra_bss',0xac,0x100))
        for name,offset,replacement in metadata:
            mutated=bytearray(clean)
            struct.pack_into('>I',mutated,offset,replacement)
            rejected(generator,home,mutated,name)
            count+=1
        valid=home/'valid.dol';valid.write_bytes(clean)
        out=home/'occupied';out.mkdir()
        canary=out/'keep.txt';canary.write_text('original')
        r=subprocess.run([str(generator),str(valid),str(out)],capture_output=True,text=True,timeout=30)
        if r.returncode==0 or canary.read_text()!='original':
            raise AssertionError('generator modified preexisting output')
        count+=1
        existing=home/'existing.dol';existing.write_text('PRESERVE')
        build=Path(__file__).with_name('make_interrupt_prefix_v50.py')
        r=subprocess.run(['python3',str(build),str(original),str(existing)],capture_output=True,text=True,timeout=30)
        if r.returncode==0 or existing.read_text()!='PRESERVE':
            raise AssertionError('private builder overwrote existing owner file')
        count+=1
    print(f'PASS: V50 {count}/{count} corrupted instruction/original SHA/DOL safety checks')
    return count


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('original_owner_dol',type=Path)
    ap.add_argument('private_generator',type=Path)
    args=ap.parse_args()
    test(args.original_owner_dol,args.private_generator)
