#!/usr/bin/env python3
"""Continue the complete original image through OSInit hardware value setup."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe
from prepare_v433_full_os_entry import patch_probe as os_probe
from prepare_v435_full_os_time import expectations as time_expectations,install as install_time,patch_probe as time_probe

EXEC=0x80523b1c;COPY=0x80004338;PERF=0x804b7964
HID4=0x804b7a30;SPEC=0x804b7a00;READ=0x804b7920;WRITE=0x804b7928;FP=0x804b7a28;STOP=0x80520700
EDGES=((0x805206bc,EXEC),)+tuple((0x805206c4+8*i,PERF+8*i) for i in range(6))+(
    (0x805206f4,HID4),(0x805206f8,SPEC),(SPEC+12,READ),(SPEC+20,WRITE),(0x805206fc,FP))
REGS=(952,956,953,954,957,958)
BODIES=((EXEC,9),(COPY,20),(HID4,20),(SPEC,10),(READ,2),(WRITE,2),(FP,2))+tuple((PERF+8*i,2) for i in range(6))

# Publish fixed stage labels and ordinals only, never private code or paths.
class PreparationError(ValueError):
    def __init__(self,stage,ordinal=0):
        self.stage=stage;self.ordinal=ordinal
        super().__init__('V439 preparation failed')

def spr(word):return ((word>>11)&31)*32+((word>>16)&31)
def require(condition,stage,ordinal=0):
    if not condition:raise PreparationError(stage,ordinal)
def read_words(data,pc,n,ordinal):
    try:return words_at(data,pc,n)
    except (ValueError,struct.error):raise PreparationError('text_mapping',ordinal) from None
def expectations(data,digest=OWNER_SHA):
    try:time_expectations(data,digest)
    except (ValueError,struct.error):raise PreparationError('prior_geometry') from None
    for i,(pc,n) in enumerate(BODIES,1):
        require(read_words(data,pc,n,i)[-1]==0x4e800020,'helper_return',i)
    tail=read_words(data,EXEC+20,1,1)[0]
    try:tail_ok=not tail&3 and direct_bl(tail|1,EXEC+20)==COPY
    except ValueError:tail_ok=False
    require(tail_ok,'exec_tail')
    for i,reg in enumerate(REGS):
        word=read_words(data,PERF+i*8,1,i+1)[0]
        require(word>>26==31 and ((word>>1)&1023)==467 and ((word>>21)&31)==3 and spr(word)==reg,'performance_helper',i+1)
    word=read_words(data,FP,1,1)[0]
    require(word>>26==63 and ((word>>1)&1023)==38 and ((word>>21)&31)==29,'fp_helper')
    rows=[]
    for i,(site,target) in enumerate(EDGES,1):
        branch=read_words(data,site,1,i)[0]
        try:ok=direct_bl(branch,site)==target
        except ValueError:ok=False
        require(ok,'call_geometry',i)
        rows.append('OsTimeEdge{'+','.join(f'0x{x:08x}u' for x in (target,site+4,branch,read_words(data,target,1,i)[0]))+'}')
    stop=read_words(data,STOP,1,0)[0]
    header=('#pragma once\n#include "wii_full_os_hardware_witness.h"\nnamespace undercover::wii::v439 {\n'
            'inline constexpr OsHardwareExpectations expected_hw{{'+',\n'.join(rows)+'},'+
            ','.join(f'0x{x:08x}u' for x in (words_at(data,COPY,1)[0],tail,stop))+'};\n}\n')
    return header,stop

OLD='        if(os_time.stage()==6u){std::cout<<"V435_TIME_RESULT frame=1 spills=12 time=1 irq_restored=1 stores=2 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
NEW='''        if(os_time.stage()==6u){
            std::cout<<"V435_TIME_RESULT frame=1 spills=12 time=1 irq_restored=1 stores=2 fallback=0 boot_verified=0"<<std::endl;
            if(!os_hw.begin(cpu)){std::cout<<"V439_HW_INVALID reason="<<os_hw.failure()<<" stage="<<os_hw.stage()<<std::endl;std::_Exit(88);}
            std::cout<<"V439_HW_BEGIN copy="<<unsigned(os_hw.copied())<<std::endl;
        }'''
OBSERVE='''    static FullOsHardwareWitness os_hw(v439::expected_hw);
    if(os_hw.active()){
        if(!os_hw.observe(addr,cpu)){std::cout<<"V439_HW_INVALID reason="<<os_hw.failure()<<" stage="<<os_hw.stage()<<std::endl;std::_Exit(88);}
        if(addr==0x80004338u){std::cout<<"V439_HW_COPY valid=1"<<std::endl;return;}
        std::cout<<"V439_HW_STAGE n="<<os_hw.stage()<<" valid=1"<<std::endl;
        if(os_hw.stage()==13u){std::cout<<"V439_HW_RESULT exec=1 perf=6 hid4=1 hid0=1 fpscr=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v435_private_time_expectations.h"','#include "v435_private_time_expectations.h"\n#include "v439_private_hw_expectations.h"')
    seam='    static FullOsTimeWitness os_time(v435::expected_time);'
    source=replace_exact(source,seam,OBSERVE+seam)
    return replace_exact(source,OLD,NEW)

def return_seam(source,word):
    pat=re.compile(r'(?m)^loc_80520700: ;\n    // 0x80520700: '+f'{word:08X}'+r'\n',re.I)
    hits=list(pat.finditer(source))
    if len(hits)!=1 or 'V439 original hardware return' in source:raise ValueError('return seam')
    at=hits[0].end();line='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80520700, ctx); // V439 original hardware return\n'
    out=source[:at]+line+source[at:]
    if out.replace(line,'',1)!=source:raise ValueError('roundtrip')
    return out

def install(data,generated,host,digest=OWNER_SHA):
    expected,stop=expectations(data,digest)
    counts=dict.fromkeys([pc for _,pc in EDGES]+[COPY],0);shards=[]
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80520700: ;$',source):shards.append((shard,source))
    for i,n in enumerate(counts.values(),1):
        require(n==1,'trace_missing' if n==0 else 'trace_duplicate',i)
    require(len(shards)==1,'return_shard_missing' if not shards else 'return_shard_duplicate')
    shard,source=shards[0]
    require(not shard.is_symlink(),'symlink')
    try:return_seam(source,stop)
    except ValueError:raise PreparationError('return_seam') from None
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v439_private_hw_expectations.h':expected,dest/'wii_full_os_hardware_witness.h':(host/'wii_full_os_hardware_witness.h').read_text(encoding='utf-8')}
    require(not dest.is_symlink() and not any(p.exists() or p.is_symlink() for p in files),'destination')
    probe=(host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8')
    for i,transform in enumerate((cache_probe,data_probe,os_probe,time_probe,patch_probe),1):
        try:probe=transform(probe)
        except ValueError:raise PreparationError('probe_seam',i) from None
    try:install_time(data,generated,host,digest)
    except (ValueError,struct.error):raise PreparationError('prior_install') from None
    # The previous data-return observer may share this shard. Read again.
    updated=return_seam(shard.read_text(encoding='utf-8'),stop)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    (dest/'wii_full_start_probe_v419.h').write_text(probe,encoding='utf-8')
    shard.write_text(updated,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except PreparationError as e:
        print(f'V440_HW_PREP stage={e.stage} ordinal={e.ordinal} verified=0')
        print('V439_HW_ROUTE installed=0');return 1
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V440_HW_PREP stage=io_or_other ordinal=0 verified=0')
        print('V439_HW_ROUTE installed=0');return 1
    print('V439_HW_ROUTE installed=1 edges=12 optional_copy=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
