#!/usr/bin/env python3
"""V62 original-code mutation, SHA, private DOL and output-boundary guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_l2poll_v62 import make, FINAL_STOP as NEW_STOP
from make_osinit_l2prefix_v61 import L2_DISABLED_STOP, L2_ENABLED_STOP, READ_L2 as MFL2CR, MFMSR
from test_osinit_guards_v57 import mutate_word, rejects


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('original_owner_wii_dol',type=Path)
    ap.add_argument('generator',type=Path)
    args=ap.parse_args()
    baseline=make(args.original_owner_wii_dol)
    CACHE_STOP = L2_DISABLED_STOP - 12
    n=0
    with tempfile.TemporaryDirectory(prefix='v62_original_image_guard_') as scratch:
        folder=Path(scratch)
        # Mutation changes to genuine helper instructions as well as test-only stops.
        pcs=(*range(CACHE_STOP,NEW_STOP+8,4),
             L2_ENABLED_STOP,L2_ENABLED_STOP+4,
             *range(MFMSR,MFL2CR+16,4))
        pcs=sorted(set(pcs))
        for pc in pcs:
            rejects(args.generator,f'original_or_terminal_{pc:08x}',mutate_word(baseline,pc),folder)
            n+=1
        for name,offset,value in (
            ('private_entry',0xe0,0x8000403c),
            ('code_address',0x48,0x80520674),
            ('code_size',0x90,0x34cc),
            ('code_file_offset',0,0x101),
            ('helper_file_offset',0x10,0x101),
            ('helper_guest_base',0x58,0x804b7920),
            ('helper_section_size',0xa0,0x160),
            ('following_text_offset',0x14,0x81d0),
            ('following_data_offset',0x1c,0x81f0),
            ('synthetic_data_file_offset',0x1c,0x101),
            ('unexpected_code_slot',0x18,0x210),
        ):
            corrupted=bytearray(baseline)
            struct.pack_into('>I',corrupted,offset,value)
            rejects(args.generator,name,corrupted,folder)
            n+=1
        truncated=baseline[:-4]
        rejects(args.generator,'private_truncated',truncated,folder)
        n+=1
        extra=baseline+b'NO_MORE'
        rejects(args.generator,'private_trailer',extra,folder)
        n+=1
        owner=bytearray(args.original_owner_wii_dol.read_bytes());owner[-1]^=1
        changed=folder/'mutated_original_owner.dol';changed.write_bytes(owner)
        try:make(changed)
        except ValueError:n+=1
        else:raise AssertionError('V62 accepted changed original-owner image')
        destination=folder/'existing_private.dol'
        destination.write_bytes(b'PRESERVE')
        builder=Path(__file__).with_name('make_osinit_l2poll_v62.py')
        result=subprocess.run(['python3',str(builder),str(args.original_owner_wii_dol),str(destination)],
                              capture_output=True,text=True,timeout=30)
        if result.returncode==0 or destination.read_bytes()!=b'PRESERVE':
            raise AssertionError('V62 builder overwrote existing image')
        n+=1
        out=folder/'existing_generated';out.mkdir()
        (out/'preserve').write_bytes(b'PRESERVE')
        image=folder/'valid_private.dol';image.write_bytes(baseline)
        result=subprocess.run([str(args.generator),str(image),str(out)],
                              capture_output=True,text=True,timeout=30)
        if result.returncode==0 or (out/'preserve').read_bytes()!=b'PRESERVE':
            raise AssertionError('V62 generator overwrote nonempty directory')
        n+=1
    print(f'PASS: V62 {n}/{n} original PPC/SHA/DOL/output safety checks')

if __name__=='__main__':main()
