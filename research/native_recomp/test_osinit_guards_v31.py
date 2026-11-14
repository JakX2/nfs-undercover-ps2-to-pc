#!/usr/bin/env python3
"""Fail-closed source-only V29 corruption, guest-call and overwrite guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_lowmem_v31 import make, STOP
from make_osinit_hid4_v30 import be32, OSINIT, ALT, PERF0 as PERF, OSREPORT as REPORT, HID0_READ as MFHID0, HID0_WRITE as MTHID0, SPEC, NONIEEE, HID4
from make_osinit_execparams_v28 import TIME, GETTIME, DISABLE, RESTORE, EXEC, SAVE, COPY


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
    with tempfile.TemporaryDirectory(prefix='v31_guards_') as d:
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
            ('old_stop_now_original_li',0,0x80520700),
            ('os_lowmem_base',0,0x80520704),
            ('os_lowmem_setbase',0,0x80520708),
            ('os_lowmem_record_clear',0,0x8052070c),
            ('os_lowmem_mode_clear',0,0x80520710),
            ('os_boot_pointer_read',0,0x80520714),
            ('os_boot_pointer_cmp',0,0x80520718),
            ('os_boot_pointer_branch',0,0x8052071c),
            ('os_record_advance',0,0x80520720),
            ('os_record_store',0,0x80520724),
            ('os_record_field_load',0,0x80520728),
            ('os_record_field_store',0,0x8052072c),
            ('os_record_firstword_load',0,0x80520730),
            ('os_record_low_byte_store',0,0x80520734),
            ('os_record_secondword_load',0,0x80520738),
            ('os_record_high_byte_store',0,0x8052073c),
            ('os_record_unconditional_branch',0,0x80520740),
            ('os_fallback_flag_read',0,0x80520744),
            ('os_fallback_flag_cmp',0,0x80520748),
            ('os_fallback_branch',0,0x8052074c),
            ('os_fallback_byte_read',0,0x80520750),
            ('os_fallback_pointer_make',0,0x80520754),
            ('os_fallback_word_store',0,0x80520758),
            ('os_fallback_pointer_store',0,0x8052075c),
            ('os_fallback_second_byte_read',0,0x80520760),
            ('os_fallback_second_word_store',0,0x80520764),
            ('os_mode_one',0,0x80520768),
            ('os_lowmem_base_reload',0,0x8052076c),
            ('os_mode_one_store',0,0x80520770),
            ('os_mem1_arena_hint_load',0,0x80520774),

            ('new_os_mmcr0_bl',0,OSINIT+0x54),
            ('new_os_mmcr1_bl',0,OSINIT+0x5c),
            ('new_os_pmc1_bl',0,OSINIT+0x64),
            ('new_os_pmc2_bl',0,OSINIT+0x6c),
            ('new_os_pmc3_bl',0,OSINIT+0x74),
            ('new_os_pmc4_bl',0,OSINIT+0x7c),
            ('hid4_call',0,0x805206f4),
            ('speculation_call',0,0x805206f8),
            ('non_ieee_call',0,0x805206fc),
            ('OSReport_stop',0,REPORT),
            ('OSReport_return',0,REPORT+4),
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
            ('mmcr0_spr',6,PERF),('mmcr0_ret',6,PERF+4),
            ('mmcr1_spr',6,PERF+8),('mmcr1_ret',6,PERF+12),
            ('pmc1_spr',6,PERF+16),('pmc1_ret',6,PERF+20),
            ('pmc2_spr',6,PERF+24),('pmc2_ret',6,PERF+28),
            ('pmc3_spr',6,PERF+32),('pmc3_ret',6,PERF+36),
            ('pmc4_spr',6,PERF+40),('pmc4_ret',6,PERF+44),
            ('hid0_read_spr',6,MFHID0),('hid0_read_ret',6,MFHID0+4),
            ('hid0_write_spr',6,MTHID0),('hid0_write_ret',6,MTHID0+4),
            ('spec_read_call',6,SPEC+0x0c),('spec_bit_ori',6,SPEC+0x10),
            ('spec_write_call',6,SPEC+0x14),('spec_return',6,SPEC+0x24),
            ('non_ieee_mtfsb1',6,NONIEEE),('non_ieee_ret',6,NONIEEE+4),
            ('hid4_mask',6,HID4+0x0c),('hid4_branch',6,HID4+0x18),
            ('hid4_mtspr_fast',6,HID4+0x1c),('hid4_report_bl',6,HID4+0x30),
            ('hid4_oris',6,HID4+0x34),('hid4_mtspr_slow',6,HID4+0x38),
            ('hid4_ret',6,HID4+0x4c),
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
    print(f'PASS: {checks} V31 original-owner boot-state opcodes, SHA, bounds and overwrite guards')


if __name__=='__main__':main()
