#!/usr/bin/env python3
"""Fail closed on every source-backed Wii OSContextInit word and layout mutation."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_context_v58 import make, OLD_STOP, NEW_STOP, CONTEXT, CONTEXT_END, OSINIT
from test_osinit_guards_v57 import mutate_word, be32, rejects


def main():
    p=argparse.ArgumentParser()
    p.add_argument('owner_original_dol',type=Path)
    p.add_argument('native_generator',type=Path)
    a=p.parse_args()
    image=make(a.owner_original_dol)
    count=0
    with tempfile.TemporaryDirectory(prefix='v58_original_guards_') as tmp:
        root=Path(tmp)
        for pc in (OLD_STOP,NEW_STOP,NEW_STOP+4,*(range(CONTEXT,CONTEXT_END,4))):
            rejects(a.native_generator,f'pc_{pc:08x}',mutate_word(image,pc),root)
            count+=1
        for name,where,value in (
            ('entry',0xe0,0x8000403c),
            ('osinit_start',0x48,0x80520674),
            ('osinit_len',0x90,0x34cc),
            ('context_external_segment',0x18,0x100),
        ):
            data=bytearray(image)
            struct.pack_into('>I',data,where,value)
            rejects(a.native_generator,name,data,root)
            count+=1
        changed=bytearray(a.owner_original_dol.read_bytes())
        changed[-1]^=1
        private=root/'bad_owner.dol';private.write_bytes(changed)
        try:make(private)
        except ValueError:count+=1
        else:raise AssertionError('modified original owner SHA accepted')
        prior=root/'existing_private.dol';prior.write_bytes(b'PRESERVE')
        script=Path(__file__).with_name('make_osinit_context_v58.py')
        r=subprocess.run(['python3',str(script),str(a.owner_original_dol),str(prior)],capture_output=True,text=True,timeout=30)
        if r.returncode==0 or prior.read_bytes()!=b'PRESERVE':
            raise AssertionError('builder overwrote an existing output')
        count+=1
        target=root/'existing_directory';target.mkdir()
        sentinel=target/'keep';sentinel.write_text('PRESERVE')
        valid=root/'valid.dol';valid.write_bytes(image)
        r=subprocess.run([str(a.native_generator),str(valid),str(target)],capture_output=True,text=True,timeout=30)
        if r.returncode==0 or sentinel.read_text()!='PRESERVE':
            raise AssertionError('native generator overwrote existing output')
        count+=1
    print(f'PASS: V58 {count}/{count} context body/owner SHA/layout/output guards')

if __name__=='__main__':
    main()
