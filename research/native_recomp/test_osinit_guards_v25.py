#!/usr/bin/env python3
"""Negative and fail-closed checks for source-only V25 OSInit-prefix fixture.

Only independently assembled synthetic PPC fixtures are shipped. Owner mode
reads private DOL locally and never writes owner text to repository paths.
"""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path

from make_osinit_prefix_v25 import make, OSINIT, OS_TIME, SAVE20, ALT_INIT
from make_start_to_dbinit_v24 import START, DBINIT, DBPRINTF


def be32(data, offset):
    return struct.unpack_from('>I',data,offset)[0]


def write32(data, offset, value):
    struct.pack_into('>I',data,offset,value)


def patch(data, section, address, opcode):
    off=be32(data,4*section)
    origin=be32(data,0x48+4*section)
    length=be32(data,0x90+4*section)
    if not origin<=address<origin+length:
        raise ValueError('test address outside intended DOL code section')
    write32(data,off+(address-origin),opcode)


def rejected(emitter, dol, out, mode):
    initial=tuple(out.iterdir()) if out.exists() else ()
    result=subprocess.run((str(emitter),str(dol),str(out),mode),
                          capture_output=True,text=True,timeout=25)
    assert result.returncode!=0,(dol.name,mode,result.stdout[-800:],result.stderr[-800:])
    assert (tuple(out.iterdir()) if out.exists() else ())==initial, 'invalid input wrote generated code'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('emitter',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    emitter=args.emitter.resolve()
    count=0
    with tempfile.TemporaryDirectory(prefix='v25_invalid_') as temp:
        root=Path(temp)
        original=bytearray(make(None))
        path=root/'synthetic.dol'
        path.write_bytes(original)
        output=root/'output'
        output.mkdir()
        for mode in ('owner','OWNER','unexpected','', 'synthetic '):
            rejected(emitter,path,output,mode)
            count+=1
        rejected(emitter,path,root/'missing_dir','synthetic'); count+=1
        (output/'keep.txt').write_text('preserve')
        rejected(emitter,path,output,'synthetic');count+=1
        assert (output/'keep.txt').read_text()=='preserve'
        (output/'keep.txt').unlink()
        def corrupt(name, mutate, owner=False):
            nonlocal count
            image=bytearray(owned if owner else original)
            mutate(image)
            bad=root/(name+'.dol');bad.write_bytes(image)
            rejected(emitter,bad,output,'owner' if owner else 'synthetic')
            count+=1
        for name,func in (
            ('bad_entry',lambda b:write32(b,0xe0,0x80004040)),
            ('zero_section',lambda b:write32(b,0,0)),
            ('text_in_header',lambda b:write32(b,0,4)),
            ('text_misaligned',lambda b:write32(b,0,0x101)),
            ('text_outside_mem1',lambda b:write32(b,0x48,0x70000000)),
            ('text_big_size',lambda b:write32(b,0x90,0x7fffffff)),
            ('file_section_overlap',lambda b:write32(b,4,be32(b,0))),
            ('guest_section_overlap',lambda b:write32(b,0x48+4,be32(b,0x48))),
            ('data_section_overlap',lambda b:write32(b,0x64,be32(b,0x48))),
            ('data_truncation',lambda b:write32(b,0xac,0x10000000)),
            ('bad_first_bl',lambda b:patch(b,0,START,0x60000000)),
            ('bad_data_bl',lambda b:patch(b,0,START+24,0x60000000)),
            ('bad_db_bl',lambda b:patch(b,0,0x80004058,0x60000000)),
            ('bad_os_bl',lambda b:patch(b,0,0x8000405c,0x60000000)),
            ('bad_db_store',lambda b:patch(b,6,DBINIT+8,0x60000000)),
            ('bad_db_return',lambda b:patch(b,6,DBINIT+12,0x60000000)),
            ('bad_os_frame',lambda b:patch(b,1,OSINIT,0x60000000)),
            ('bad_os_helper_bl',lambda b:patch(b,1,OSINIT+0x10,0x60000000)),
            ('bad_os_marker',lambda b:patch(b,1,OSINIT+0x1c,0x60000000)),
            ('bad_os_time_bl',lambda b:patch(b,1,OSINIT+0x20,0x60000000)),
            ('bad_os_boundary_return',lambda b:patch(b,1,OSINIT+0x24,0x60000000)),
            ('bad_saved_reg',lambda b:patch(b,5,SAVE20,0x60000000)),
            ('bad_save_return',lambda b:patch(b,5,SAVE20+4,0x60000000)),
            ('bad_time_stop',lambda b:patch(b,5,OS_TIME,0x60000000)),
            ('bad_time_return',lambda b:patch(b,5,OS_TIME+4,0x60000000)),
            ('bad_dbprintf_stop',lambda b:patch(b,6,DBPRINTF,0x60000000)),
        ):
            corrupt(name,func)
        for length in (0,1,127,255,len(original)-1):
            bad=root/(f'truncated_{length}.dol')
            bad.write_bytes(original[:length])
            rejected(emitter,bad,output,'synthetic')
            count+=1
        if args.owner_dol:
            data=bytearray(args.owner_dol.read_bytes());data[-1]^=1
            tampered=root/'tampered_original.dol';tampered.write_bytes(data)
            try:
                make(tampered)
            except ValueError:
                count+=1
            else:
                raise AssertionError('owner original SHA mismatch accepted')
            owned=bytearray(make(args.owner_dol))
            for name,func in (
                ('owner_prologue',lambda b:patch(b,1,OSINIT,0x60000000)),
                ('owner_init_flag',lambda b:patch(b,1,OSINIT+0x34,0x60000000)),
                ('owner_save_call',lambda b:patch(b,1,OSINIT+0x10,0x60000000)),
                ('owner_time_call',lambda b:patch(b,1,OSINIT+0x38,0x60000000)),
                ('owner_save_gpr',lambda b:patch(b,5,SAVE20,0x60000000)),
                ('owner_save_return',lambda b:patch(b,5,SAVE20+48,0x60000000)),
                ('owner_alt_init_guard',lambda b:patch(b,1,ALT_INIT,0x60000000)),
                ('owner_time_stop',lambda b:patch(b,5,OS_TIME,0x60000000)),
                ('owner_time_return',lambda b:patch(b,5,OS_TIME+4,0x60000000)),
            ):
                corrupt(name,func,owner=True)
    print('PASS:',count,'V25 fail-closed bounds, corrupted-function, owner SHA and overwrite checks')


if __name__=='__main__':
    main()
