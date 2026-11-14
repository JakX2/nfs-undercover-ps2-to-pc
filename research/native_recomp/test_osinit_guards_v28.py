#!/usr/bin/env python3
"""Fail-closed source-only V28 corruption, guest-call and overwrite guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_execparams_v28 import (make, be32, OSINIT, STOP, ALT, TIME,
                                       GETTIME, DISABLE, RESTORE, EXEC, SAVE, COPY)


def patch(blob, section, address, opcode):
    off=be32(blob,section*4)
    start=be32(blob,0x48+section*4)
    count=be32(blob,0x90+section*4)
    if not start<=address<start+count:
        raise ValueError('corruption request is outside selected guest code range')
    struct.pack_into('>I',blob,off+address-start,opcode)


def rejects(generator, file, out):
    before=sorted(p.name for p in out.iterdir()) if out.exists() else []
    p=subprocess.run([str(generator),str(file),str(out)],
                     capture_output=True,text=True,timeout=30)
    assert p.returncode!=0,(file.name,p.stdout[-500:],p.stderr[-500:])
    after=sorted(p.name for p in out.iterdir()) if out.exists() else []
    assert after==before,'rejected file unexpectedly changed output directory'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('owner_dol',type=Path)
    ap.add_argument('generator',type=Path)
    args=ap.parse_args()
    checks=0
    with tempfile.TemporaryDirectory(prefix='v28_guards_') as d:
        root=Path(d);output=root/'empty';output.mkdir()
        original=make(args.owner_dol)
        sha_mutation=bytearray(args.owner_dol.read_bytes());sha_mutation[-1]^=1
        corrupted=root/'mutated_owner.dol';corrupted.write_bytes(sha_mutation)
        try:make(corrupted)
        except ValueError:checks+=1
        else:raise AssertionError('modified original owner executable passed SHA')
        def bad(name,change):
            nonlocal checks
            image=bytearray(original)
            change(image)
            path=root/(name+'.dol');path.write_bytes(image)
            rejects(args.generator,path,output)
            checks+=1
            return path
        for name,index,address in (
            ('original_start_prologue',0,OSINIT),
            ('save_callsite',0,OSINIT+0x10),
            ('initflag_store',0,OSINIT+0x34),
            ('time_callsite',0,OSINIT+0x38),
            ('low_time_store',0,OSINIT+0x3c),
            ('high_time_store',0,OSINIT+0x40),
            ('disable_callsite',0,OSINIT+0x44),
            ('execparams_callsite',0,OSINIT+0x4c),
            ('continuation_syscall',0,STOP),
            ('alt_branch_syscall',0,ALT),
            ('alt_branch_return',0,ALT+4),
            ('first_timebase_high',1,GETTIME),
            ('timebase_low',1,GETTIME+4),
            ('second_timebase_high',1,GETTIME+8),
            ('sys_time_gettime_call',1,TIME+0x20),
            ('sys_time_restore_call',1,TIME+0x3c),
            ('disable_return',2,DISABLE+16),
            ('restore_return',2,RESTORE+32),
            ('execparams_source_pointer',3,EXEC+4),
            ('execparams_copy_length',3,EXEC+16),
            ('execparams_copy_branch',3,EXEC+20),
            ('execparams_zero_constant',3,EXEC+24),
            ('execparams_zero_store',3,EXEC+28),
            ('execparams_return',3,EXEC+32),
            ('savegpr_return',4,SAVE+48),
            ('memcpy_return',5,COPY+76),
        ):
            bad(name,lambda b,i=index,a=address:patch(b,i,a,0x60000000))
        for name,off,value in (
            ('bad_entry',0xe0,STOP),
            ('zero_section',0,0),
            ('short_section',0x90,4),
            ('bad_section_alignment',0,0x101),
            ('wrong_guest_address',0x48,0x80520674),
            ('overlap_section',0x48+4,OSINIT),
            ('section_spills_mem1',0x48+20,0x817fffff),
            ('invalid_extra_data',0x1c,0x100),
        ):
            bad(name,lambda b,o=off,v=value:struct.pack_into('>I',b,o,v))
        for n in (0,100,255,len(original)-1):
            bad('truncated_'+str(n),lambda b,n=n:b.__delitem__(slice(n,None)))
        (output/'preserve.txt').write_text('untouched')
        bad('no_output_overwrite',lambda b:patch(b,0,OSINIT,0x60000000))
        assert (output/'preserve.txt').read_text()=='untouched'
        checks+=1
        rejects(args.generator,root/'no_output_overwrite.dol',root/'missing-output-dir')
        checks+=1
    print(f'PASS: {checks} V28 original-owner SHA, malformed-slice and fail-closed overwrite guards')


if __name__=='__main__':main()
