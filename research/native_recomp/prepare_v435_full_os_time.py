#!/usr/bin/env python3
"""Extend the authenticated complete-image startup into cold OSInit time."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v433_full_os_entry import expectations as os_expectations,install as install_os,patch_probe as os_probe
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import patch_probe as data_probe

OS=0x80520670
SAVE=0x805450e8
TIME=0x8052a844
GET=0x8052a824
DISABLE=0x805265ac
RESTORE=0x805265d4
EDGES=((OS+0x10,SAVE),(OS+0x38,TIME),(TIME+0x18,DISABLE),
       (TIME+0x20,GET),(TIME+0x3c,RESTORE),(OS+0x44,DISABLE))
BODIES=((SAVE,13),(TIME,25),(GET,6),(DISABLE,5),(RESTORE,9))

def expectations(data,digest=OWNER_SHA):
    os_expectations(data,digest)
    for pc,count in BODIES:
        if words_at(data,pc,count)[-1]!=0x4e800020:raise ValueError('helper return')
    # Authenticate the two stores by decoded source register and destination.
    stores=set()
    for word in words_at(data,OS+0x3c,2):
        if word>>26!=36 or (word>>16)&31!=13:raise ValueError('timestamp store')
        disp=word&0xffff
        if disp&0x8000:disp-=0x10000
        stores.add(((word>>21)&31,0x8070e8e0+disp))
    if stores!={(3,0x8070db30),(4,0x8070db34)}:raise ValueError('timestamp destination')
    rows=[]
    for site,target in EDGES:
        branch=words_at(data,site,1)[0]
        if direct_bl(branch,site)!=target:raise ValueError('time call geometry')
        rows.append('OsTimeEdge{'+','.join(f'0x{x:08x}u' for x in (target,site+4,branch,words_at(data,target,1)[0]))+'}')
    return ('#pragma once\n#include "wii_full_os_time_witness.h"\n'
            'namespace undercover::wii::v435 {\ninline constexpr OsTimeExpectations expected_time{{'
            +',\n'.join(rows)+'}};\n}\n')

OLD='        std::cout<<"V433_OS_RESULT db_return=1 debug_stores=4 os_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);'
NEW='''        std::cout<<"V433_OS_RESULT db_return=1 debug_stores=4 os_entry=1 fallback=0 boot_verified=0"<<std::endl;
        if(!os_time.begin(cpu)){std::cout<<"V435_TIME_INVALID reason="<<os_time.failure()<<" stage="<<os_time.stage()<<std::endl;std::_Exit(87);}
        return; // execute original cold OSInit prologue'''
OBSERVE='''    static FullOsTimeWitness os_time(v435::expected_time);
    if(os_time.active()){
        if(!os_time.observe(addr,cpu)){std::cout<<"V435_TIME_INVALID reason="<<os_time.failure()<<" stage="<<os_time.stage()<<std::endl;std::_Exit(87);}
        std::cout<<"V435_TIME_STAGE n="<<os_time.stage()<<" valid=1"<<std::endl;
        if(os_time.stage()==6u){std::cout<<"V435_TIME_RESULT frame=1 spills=12 time=1 irq_restored=1 stores=2 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v433_private_os_expectations.h"','#include "v433_private_os_expectations.h"\n#include "v435_private_time_expectations.h"')
    seam='    static FullOsEntryWitness os_entry(v433::expected_os);'
    source=replace_exact(source,seam,OBSERVE+seam)
    return replace_exact(source,OLD,NEW)

def install(data,generated,host,digest=OWNER_SHA):
    expected=expectations(data,digest)
    counts=dict.fromkeys((pc for _,pc in EDGES),0)
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:
            counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('missing unique AOT time helper')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v435_private_time_expectations.h':expected,dest/'wii_full_os_time_witness.h':(host/'wii_full_os_time_witness.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination exists')
    probe=patch_probe(os_probe(data_probe(cache_probe((host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8')))))
    install_os(data,generated,host,digest)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    (dest/'wii_full_start_probe_v419.h').write_text(probe,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V435_TIME_ROUTE installed=0');return 1
    print('V435_TIME_ROUTE installed=1 edges=6 stores=2 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
