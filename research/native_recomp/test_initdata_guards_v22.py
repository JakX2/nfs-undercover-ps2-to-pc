#!/usr/bin/env python3
"""Original-free malformed-table and owner-local startup-slice guard tests."""
import argparse
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
from make_initdata_slice_v22 import (
    ENTRY, END, STOP, TABLE, TABLE_LENGTH, FILL, FLUSH, COPY, SET,
    check_code, get_section, make, make_synthetic_table, parse_table,
)


def fake_code():
    # Entirely synthetic PPC fixture, not copied from the game. Only the
    # tested callsite/return structure is preserved, not the game instructions.
    body=bytearray(struct.pack('>I',0x60000000)*((END-ENTRY)//4))
    for pc,target in ((ENTRY+72,COPY),(ENTRY+84,FLUSH),(ENTRY+128,SET),(SET+20,FILL)):
        displacement=(target-pc)&0x03fffffc
        struct.pack_into('>I',body,pc-ENTRY,0x48000001|displacement)
    for pc,length in ((ENTRY,168),(FLUSH,52),(COPY,80),(FILL,180),(SET,48)):
        struct.pack_into('>I',body,pc-ENTRY+length-4,0x4e800020)
    return bytes(body)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('generator',type=Path)
    ap.add_argument('--owner-dol',type=Path)
    args=ap.parse_args()
    assert args.generator.is_file()
    checks=0

    def verify(condition,reason):
        nonlocal checks
        assert condition,reason
        checks+=1

    def rejected(callback,exc=(ValueError,struct.error)):
        nonlocal checks
        try:
            callback()
        except exc:
            checks+=1
        else:
            raise AssertionError('invalid input was accepted')

    table=make_synthetic_table()
    copies,zeros=parse_table(table)
    verify(copies==[(0x80031000,0x80032000,65)],'unexpected synthetic copy fixture')
    verify(zeros==[(0x80033000,96),(0x80033100,7)],'unexpected synthetic BSS fixture')
    rejected(lambda:parse_table(table[:-1]))
    for field,value in ((8,0x02000000),(0,0),(4,0),(0,0x70000000),
                        (4,0x70000000),(4,0x817FFFF0),(0,0x817FFFF0),(0x94,0x02000000),(0x90,0),
                        (0x90,0x70000000),(0x90,0x817FFFF0)):
        damaged=bytearray(table)
        struct.pack_into('>I',damaged,field,value)
        rejected(lambda d=bytes(damaged):parse_table(d))
    # Missing terminators: all copy rows and all BSS rows have lengths.
    bad=bytearray(table)
    for offset in range(0,0x90,12):
        struct.pack_into('>III',bad,offset,0x80031000,0x80032000,1)
    rejected(lambda:parse_table(bytes(bad)))
    bad=bytearray(table)
    for offset in range(0x90,TABLE_LENGTH,8):
        struct.pack_into('>II',bad,offset,0x80033000,1)
    rejected(lambda:parse_table(bytes(bad)))

    code=fake_code()
    check_code(code)
    checks+=1
    rejected(lambda:check_code(code[:-4]))
    for address in (ENTRY+72,ENTRY+84,ENTRY+128,SET+20,ENTRY+164,FLUSH+48,FILL+176,SET+44):
        bad=bytearray(code)
        struct.pack_into('>I',bad,address-ENTRY,0x60000000)
        rejected(lambda b=bytes(bad):check_code(b))
    bad=bytearray(code)
    struct.pack_into('>I',bad,ENTRY+72-ENTRY,0x48000005)
    rejected(lambda:check_code(bytes(bad)))
    rejected(lambda:get_section(b'',ENTRY,168))
    rejected(lambda:get_section(b'\0'*256,ENTRY,168))
    rejected(lambda:get_section(b'\0'*256,ENTRY+1,168))
    rejected(lambda:get_section(b'\0'*256,ENTRY,166))

    with tempfile.TemporaryDirectory(prefix='v22_guards_') as temp:
        directory=Path(temp)
        garbage=directory/'invalid-owner.dol'
        garbage.write_bytes(code)
        rejected(lambda:make(garbage,'original'))
        rejected(lambda:make(garbage,'synthetic'))
        output=directory/'must-not-overwrite.dol'
        output.write_bytes(b'keep')
        p=subprocess.run(['python3',str(Path(__file__).with_name('make_initdata_slice_v22.py')),
                          str(garbage),str(output)],capture_output=True,text=True,timeout=10)
        verify(p.returncode!=0 and output.read_bytes()==b'keep','overwrite protection failed')
        # Generated-code output must be an existing empty directory.
        dummy=directory/'dummy.dol'
        dummy.write_bytes(b'\0'*256)
        dest=directory/'output';dest.mkdir(); (dest/'keep.txt').write_text('keep')
        p=subprocess.run([str(args.generator),str(dummy),str(dest)],capture_output=True,text=True,timeout=10)
        verify(p.returncode!=0 and (dest/'keep.txt').read_text()=='keep','generator overwrote nonempty destination')
        p=subprocess.run([str(args.generator),str(dummy),str(directory/'missing')],capture_output=True,text=True,timeout=10)
        verify(p.returncode!=0 and not (directory/'missing').exists(),'generator created missing output dir')
        if args.owner_dol:
            owner=args.owner_dol.read_bytes()
            original=make(args.owner_dol,'original')
            synthetic=make(args.owner_dol,'synthetic')
            verify(original!=synthetic,'synthetic table did not differ from owner table')
            verify(original[:0x100]==synthetic[:0x100],'fixture layout differs by mode')
            parse_table(get_section(owner,TABLE,TABLE_LENGTH))
            checks+=1
            src=bytearray(owner)
            src[0x100]^=1
            fake_owner=directory/'wrong-hash.dol';fake_owner.write_bytes(src)
            rejected(lambda:make(fake_owner,'original'))
            verify(hashlib.sha256(owner).hexdigest()!=hashlib.sha256(src).hexdigest(), 'SHA test setup invalid')
    print(f'PASS: {checks} source-only V22 malformed-data and overwrite guards')


if __name__=='__main__':
    main()
