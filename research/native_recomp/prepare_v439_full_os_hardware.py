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

def spr(word):return ((word>>11)&31)*32+((word>>16)&31)
def expectations(data,digest=OWNER_SHA):
    time_expectations(data,digest)
    for pc,n in BODIES:
        if words_at(data,pc,n)[-1]!=0x4e800020:raise ValueError('helper return')
    tail=words_at(data,EXEC+20,1)[0]
    if tail&3 or direct_bl(tail|1,EXEC+20)!=COPY:raise ValueError('exec tail')
    for i,reg in enumerate(REGS):
        word=words_at(data,PERF+i*8,1)[0]
        if word>>26!=31 or ((word>>1)&1023)!=467 or ((word>>21)&31)!=3 or spr(word)!=reg:raise ValueError('performance helper')
    word=words_at(data,FP,1)[0]
    if word>>26!=63 or ((word>>1)&1023)!=38 or ((word>>21)&31)!=29:raise ValueError('FP helper')
    rows=[]
    for site,target in EDGES:
        branch=words_at(data,site,1)[0]
        if direct_bl(branch,site)!=target:raise ValueError('hardware call geometry')
        rows.append('OsTimeEdge{'+','.join(f'0x{x:08x}u' for x in (target,site+4,branch,words_at(data,target,1)[0]))+'}')
    stop=words_at(data,STOP,1)[0]
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
    counts=dict.fromkeys({pc for _,pc in EDGES}|{COPY},0);shards=[]
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80520700: ;$',source):shards.append((shard,source))
    if any(n!=1 for n in counts.values()) or len(shards)!=1:raise ValueError('native hardware coverage')
    shard,source=shards[0]
    if shard.is_symlink():raise ValueError('symlink')
    return_seam(source,stop)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v439_private_hw_expectations.h':expected,dest/'wii_full_os_hardware_witness.h':(host/'wii_full_os_hardware_witness.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination exists')
    probe=(host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8')
    for transform in (cache_probe,data_probe,os_probe,time_probe,patch_probe):
        probe=transform(probe)
    install_time(data,generated,host,digest)
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
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V439_HW_ROUTE installed=0');return 1
    print('V439_HW_ROUTE installed=1 edges=12 optional_copy=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
