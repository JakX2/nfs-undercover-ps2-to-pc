#!/usr/bin/env python3
"""Fail-closed source-backed V59 OSCacheInit, original L1 helper and image guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_cache_l1_v59 import (
    make, OSINIT_STOP, CACHE, CACHE_STOP, IC_ENABLE, DC_ENABLE
)
from test_osinit_guards_v57 import mutate_word, rejects


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_original_wii_dol',type=Path)
    ap.add_argument('native_generator',type=Path)
    args=ap.parse_args()
    baseline=make(args.owner_original_wii_dol)
    count=0
    with tempfile.TemporaryDirectory(prefix='v59_original_guards_') as tmp:
        where=Path(tmp)
        pcs=(OSINIT_STOP,
             *(range(CACHE,CACHE_STOP+8,4)),
             *(range(IC_ENABLE,IC_ENABLE+0x14,4)),
             *(range(DC_ENABLE,DC_ENABLE+0x14,4)))
        assert len(set(pcs))==len(pcs)
        for pc in pcs:
            rejects(args.native_generator,f'original_or_stop_{pc:08x}',mutate_word(baseline,pc),where)
            count+=1
        for name,header,value in (
            ('entry',0xe0,0x8000403c),
            ('osinit_address',0x48,0x80520674),
            ('osinit_length',0x90,0x34cc),
            ('osinit_data_offset',0,0x101),
            ('helper_segment',0x10,0x101),
            ('synthetic_data_offset',0x1c,0x101),
        ):
            corrupt=bytearray(baseline)
            struct.pack_into('>I',corrupt,header,value)
            rejects(args.native_generator,name,corrupt,where)
            count+=1
        owner=bytearray(args.owner_original_wii_dol.read_bytes());owner[-1]^=1
        bad=where/'modified_owner.dol';bad.write_bytes(owner)
        try:make(bad)
        except ValueError:count+=1
        else:raise AssertionError('modified original Wii DOL passed owner SHA-256 check')
        existing=where/'existing_private.dol';existing.write_bytes(b'PRESERVE')
        builder=Path(__file__).with_name('make_osinit_cache_l1_v59.py')
        result=subprocess.run(['python3',str(builder),str(args.owner_original_wii_dol),str(existing)],
                              capture_output=True,text=True,timeout=30)
        if result.returncode==0 or existing.read_bytes()!=b'PRESERVE':
            raise AssertionError('V59 builder overwrote existing private test image')
        count+=1
        output=where/'existing_output';output.mkdir()
        (output/'preserve').write_bytes(b'PRESERVE')
        image=where/'valid_private.dol';image.write_bytes(baseline)
        result=subprocess.run([str(args.native_generator),str(image),str(output)],
                              capture_output=True,text=True,timeout=30)
        if result.returncode==0 or (output/'preserve').read_bytes()!=b'PRESERVE':
            raise AssertionError('V59 generator overwrote nonempty output directory')
        count+=1
    print(f'PASS: V59 {count}/{count} original-body/SHA/DOL-geometry/safe-output guards')

if __name__=='__main__':main()
