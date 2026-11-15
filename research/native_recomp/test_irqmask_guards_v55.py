#!/usr/bin/env python3
"""Original Wii IRQ mask loop SHA/opcode/fixture/output safety regression guards."""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
from make_irqmask_loop_v55 import make


def u32(data,index):return int.from_bytes(data[index:index+4],'big')


def check(owner:Path,gen:Path):
    valid=make(owner)
    original=owner.read_bytes()
    count=0
    with tempfile.TemporaryDirectory(prefix='private_v55_guards_') as tmp:
        folder=Path(tmp)
        image=folder/'mutated.dol'
        output=folder/'out'
        output.mkdir()

        def reject(mutated:bytes,why:str):
            nonlocal count
            image.write_bytes(mutated)
            run=subprocess.run([str(gen),str(image),str(output)],capture_output=True,text=True,timeout=10)
            if run.returncode==0 or list(output.iterdir()):
                raise AssertionError(f'V55 accepted corrupted private original image: {why}')
            count+=1

        # All original interrupt, mask, interrupt-disable and memset/fill words;
        # the synthetic terminal syscall and blr are pinned as well.
        for section in range(4):
            at=u32(valid,4*section)
            length=u32(valid,0x90+4*section)
            for index in range(at,at+length,4):
                mutated=bytearray(valid)
                mutated[index+(index//4)%4]^=1
                reject(mutated,f'original/synthetic PPC section {section} word {index:#x}')

        for head,count_words in ((0,7),(0x48,7),(0x90,7),(0x1c,11),(0x64,11),(0xac,11)):
            for i in range(count_words):
                mutated=bytearray(valid)
                mutated[head+4*i+3]^=1
                reject(mutated,f'private DOL descriptor {head:#x} {i}')
        mutated=bytearray(valid);mutated[0xe3]^=1
        reject(mutated,'guest original entrypoint')
        reject(valid[:-1],'truncated private Wii fixture')
        reject(valid+b'EXTRA','appended content to private Wii fixture')

        modified_owner=folder/'owner_corrupt.dol'
        for data in (bytes([original[0]^1])+original[1:],original+b'EXTRA'):
            modified_owner.write_bytes(data)
            try:make(modified_owner)
            except ValueError:count+=1
            else:raise AssertionError('source builder accepted wrong SHA owner DOL')

        sentinel=folder/'owner_canary.dol';sentinel.write_bytes(b'CANARY')
        source_script=Path(__file__).with_name('make_irqmask_loop_v55.py')
        run=subprocess.run([sys.executable,str(source_script),str(owner),str(sentinel)],capture_output=True,text=True,timeout=10)
        if run.returncode==0 or sentinel.read_bytes()!=b'CANARY':raise AssertionError('builder overwrote existing private output')
        count+=1

        image.write_bytes(valid)
        sentinel=output/'canary.txt';sentinel.write_bytes(b'CANARY')
        run=subprocess.run([str(gen),str(image),str(output)],capture_output=True,text=True,timeout=10)
        if run.returncode==0 or sentinel.read_bytes()!=b'CANARY':raise AssertionError('generator overwrote existing private output')
        count+=1
    print(f'PASS: {count}/{count} V55 instruction-mutation, SHA, DOL geometry and overwrite safety checks')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('original_owner_dol',type=Path)
    parser.add_argument('native_generator',type=Path)
    args=parser.parse_args()
    check(args.original_owner_dol,args.native_generator)
