#!/usr/bin/env python3
"""Fail-closed source-only V29 corruption, guest-call and overwrite guards."""
import argparse
import struct
import subprocess
import tempfile
from pathlib import Path
from make_osinit_vectorcopy_v42 import (
    make, FIRST_DEBUG as FIRSTSTOP, SECOND_DEBUG as SECONDSTOP,
    CACHE_STOP as STOP, PRIVATE_DATA_GUEST as ORACLE, TEMPLATE_SIZE,
)
from make_osinit_dbmark_v40 import ENTRY as EXCEPTION, MARK
from make_osinit_exception_v39 import EXC_DEBUG_STOP as DEBUGSTOP, EXC_NORMAL_STOP as OLDSTOP, NEXT_OS_STOP as NEXTSTOP, EXC_SOURCE_WORD as TEMPLATE
from make_osinit_ipc_v38 import IPC
from make_osinit_mem2_v37 import MEM2_LO, MEM2_HI
from make_osinit_arena_v32 import LO, HI
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
    with tempfile.TemporaryDirectory(prefix='v42_vectorcopy_guards_') as d:
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
            *[(f'exception_prefix_{(a-EXCEPTION)//4:02d}',0,a)
              for a in range(EXCEPTION,DEBUGSTOP,4)],
            *[(f'exception_setup_{(a-DEBUGSTOP-8)//4:02d}',0,a)
              for a in range(DEBUGSTOP+8,OLDSTOP,4)],
            *[(f'exception_mark_first_{(a-OLDSTOP)//4:02d}',0,a) for a in range(OLDSTOP,FIRSTSTOP,4)],
            *[(f'exception_mark_second_{(a-FIRSTSTOP-8)//4:02d}',0,a) for a in range(FIRSTSTOP+8,0x80520D80,4)],
            *[(f'original_vector_copy_{(a-0x80520D80)//4:02d}',0,a) for a in range(0x80520D80,STOP,4)],
            *[(f'original_mark_helper_word_{i}',6,MARK+4*i) for i in range(6)],
            ('first_exception_mark_stop',0,FIRSTSTOP),
            ('first_debug_following_original_branch',0,FIRSTSTOP+4),
            ('second_exception_debug_stop',0,SECONDSTOP),
            ('second_debug_following_original_word',0,SECONDSTOP+4),
            ('save_callsite',0,OSINIT+0x10),
            ('initflag_store',0,OSINIT+0x34),
            ('time_callsite',0,OSINIT+0x38),
            ('low_time_store',0,OSINIT+0x3c),
            ('high_time_store',0,OSINIT+0x40),
            ('disable_callsite',0,OSINIT+0x44),
            ('execparams_callsite',0,OSINIT+0x4c),
            ('continuation_syscall',0,STOP),
            ('ipc_original_bl',0,0x805208a4),
            ('original_exception_bl',0,0x805208a8),
            ('unverified_next_OSInit_stop',0,NEXTSTOP),
            ('unverified_next_OSInit_return',0,NEXTSTOP+4),
            ('original_exception_debug_stop',0,DEBUGSTOP),
            ('original_exception_debug_return',0,DEBUGSTOP+4),
            ('original_exception_normal_return',0,STOP+4),
            ('original_exception_template_word',0,TEMPLATE),
            ('original_exception_analyzer_guard_A',0,0x80520E98),
            ('original_exception_analyzer_guard_B',0,0x80520E9C),
            ('original_exception_analyzer_guard_C',0,0x80520EC0),
            ('original_exception_analyzer_guard_D',0,0x80520F58),
            ('ipc_lis',1,IPC),
            ('ipc_first_load',1,IPC+4),
            ('ipc_first_store',1,IPC+8),
            ('ipc_second_load',1,IPC+12),
            ('ipc_second_store',1,IPC+16),
            ('ipc_return',1,IPC+20),
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

            # V38: every one of the 40 original Wii arena-selection PPC words
            # is verified by a private, owner-source-pinned code hash.
            ('arena_select_00',0,0x80520778),
            ('arena_select_01',0,0x8052077C),
            ('arena_select_02',0,0x80520780),
            ('arena_select_03',0,0x80520784),
            ('arena_select_04',0,0x80520788),
            ('arena_select_05',0,0x8052078C),
            ('arena_select_06',0,0x80520790),
            ('arena_select_07',0,0x80520794),
            ('arena_select_08',0,0x80520798),
            ('arena_select_09',0,0x8052079C),
            ('arena_select_10',0,0x805207A0),
            ('arena_select_11',0,0x805207A4),
            ('arena_select_12',0,0x805207A8),
            ('arena_select_13',0,0x805207AC),
            ('arena_select_14',0,0x805207B0),
            ('arena_select_15',0,0x805207B4),
            ('arena_select_16',0,0x805207B8),
            ('arena_select_17',0,0x805207BC),
            ('arena_select_18',0,0x805207C0),
            ('arena_select_19',0,0x805207C4),
            ('arena_select_20',0,0x805207C8),
            ('arena_select_21',0,0x805207CC),
            ('arena_select_22',0,0x805207D0),
            ('arena_select_23',0,0x805207D4),
            ('arena_select_24',0,0x805207D8),
            ('arena_select_25',0,0x805207DC),
            ('arena_select_26',0,0x805207E0),
            ('arena_select_27',0,0x805207E4),
            ('arena_select_28',0,0x805207E8),
            ('arena_select_29',0,0x805207EC),
            ('arena_select_30',0,0x805207F0),
            ('arena_select_31',0,0x805207F4),
            ('arena_select_32',0,0x805207F8),
            ('arena_select_33',0,0x805207FC),
            ('arena_select_34',0,0x80520800),
            ('arena_select_35',0,0x80520804),
            ('arena_select_36',0,0x80520808),
            ('arena_select_37',0,0x8052080C),
            ('arena_select_38',0,0x80520810),
            ('arena_select_39',0,0x80520814),
            ('arena_lo_store',0,LO),('arena_lo_return',0,LO+4),
            ('arena_hi_store',0,HI),('arena_hi_return',0,HI+4),
            ('mem2_source_00',0,0x80520818),
            ('mem2_source_01',0,0x8052081c),
            ('mem2_source_02',0,0x80520820),
            ('mem2_source_03',0,0x80520824),
            ('mem2_source_04',0,0x80520828),
            ('mem2_source_05',0,0x8052082c),
            ('mem2_source_06',0,0x80520830),
            ('mem2_source_07',0,0x80520834),
            ('mem2_source_08',0,0x80520838),
            ('mem2_source_09',0,0x8052083c),
            ('mem2_source_10',0,0x80520840),
            ('mem2_source_11',0,0x80520844),
            ('mem2_source_12',0,0x80520848),
            ('mem2_source_13',0,0x8052084c),
            ('mem2_source_14',0,0x80520850),
            ('mem2_source_15',0,0x80520854),
            ('mem2_source_16',0,0x80520858),
            ('mem2_source_17',0,0x8052085c),
            ('mem2_source_18',0,0x80520860),
            ('mem2_source_19',0,0x80520864),
            ('mem2_source_20',0,0x80520868),
            ('mem2_source_21',0,0x8052086c),
            ('mem2_source_22',0,0x80520870),
            ('mem2_source_23',0,0x80520874),
            ('mem2_source_24',0,0x80520878),
            ('mem2_source_25',0,0x8052087c),
            ('mem2_source_26',0,0x80520880),
            ('mem2_source_27',0,0x80520884),
            ('mem2_source_28',0,0x80520888),
            ('mem2_source_29',0,0x8052088c),
            ('mem2_source_30',0,0x80520890),
            ('mem2_source_31',0,0x80520894),
            ('mem2_source_32',0,0x80520898),
            ('mem2_source_33',0,0x8052089c),
            ('mem2_source_34',0,0x805208a0),
            ('mem2_low_store',0,MEM2_LO),('mem2_low_return',0,MEM2_LO+4),
            ('mem2_high_store',0,MEM2_HI),('mem2_high_return',0,MEM2_HI+4),
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
            ('execparams_source_pointer',0,EXEC+4),
            ('execparams_copy_length',0,EXEC+16),
            ('execparams_copy_branch',0,EXEC+20),
            ('execparams_zero_constant',0,EXEC+24),
            ('execparams_zero_store',0,EXEC+28),
            ('execparams_return',0,EXEC+32),
            ('savegpr_return',3,SAVE+48),
            ('memcpy_return',4,COPY+76),
            ('mmcr0_spr',5,PERF),('mmcr0_ret',5,PERF+4),
            ('mmcr1_spr',5,PERF+8),('mmcr1_ret',5,PERF+12),
            ('pmc1_spr',5,PERF+16),('pmc1_ret',5,PERF+20),
            ('pmc2_spr',5,PERF+24),('pmc2_ret',5,PERF+28),
            ('pmc3_spr',5,PERF+32),('pmc3_ret',5,PERF+36),
            ('pmc4_spr',5,PERF+40),('pmc4_ret',5,PERF+44),
            ('hid0_read_spr',5,MFHID0),('hid0_read_ret',5,MFHID0+4),
            ('hid0_write_spr',5,MTHID0),('hid0_write_ret',5,MTHID0+4),
            ('spec_read_call',5,SPEC+0x0c),('spec_bit_ori',5,SPEC+0x10),
            ('spec_write_call',5,SPEC+0x14),('spec_return',5,SPEC+0x24),
            ('non_ieee_mtfsb1',5,NONIEEE),('non_ieee_ret',5,NONIEEE+4),
            ('hid4_mask',5,HID4+0x0c),('hid4_branch',5,HID4+0x18),
            ('hid4_mtspr_fast',5,HID4+0x1c),('hid4_report_bl',5,HID4+0x30),
            ('hid4_oris',5,HID4+0x34),('hid4_mtspr_slow',5,HID4+0x38),
            ('hid4_ret',5,HID4+0x4c),
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
            ('invalid_private_data_offset',0x1c,0x100),
            ('wrong_template_data_guest',0x64,0x90050004),
            ('wrong_template_data_length',0xac,0x94),
            ('invalid_extra_data_section',0x20,0x100),
        ):
            bad(name,lambda b,o=off,v=value:struct.pack_into('>I',b,o,v))
        for i in (0,4,36,92,TEMPLATE_SIZE-1):
            bad('private_template_oracle_'+str(i),
                lambda b,i=i:b.__setitem__(be32(b,0x1c)+i,b[be32(b,0x1c)+i]^0xff))
        for n in (0,100,255,len(original)-1):
            bad('truncated_'+str(n),lambda b,n=n:b.__delitem__(slice(n,None)))
        (output/'preserve.txt').write_text('untouched')
        bad('no_output_overwrite',lambda b:patch(b,0,OSINIT,0x60000000))
        assert (output/'preserve.txt').read_text()=='untouched'
        checks+=1
        rejects(args.generator,root/'no_output_overwrite.dol',root/'missing-output-dir')
        checks+=1
    print(f'PASS: {checks} V42 original-owner exception-vector copy opcodes, SHA, bounds and overwrite guards')


if __name__=='__main__':main()
