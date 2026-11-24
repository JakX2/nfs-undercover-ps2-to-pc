#!/usr/bin/env python3
"""Continue the private complete-image data witness to original OSInit entry."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v428_full_cache import patch_probe as cache_probe
from prepare_v430_full_data import expectations as data_expectations,install as install_data,patch_probe as data_probe

DB=0x804e5020
OS=0x80520670
DB_CALL=0x80004158
OS_CALL=0x8000415c

def expectations(data:bytes,digest:str=OWNER_SHA)->str:
    data_expectations(data,digest)
    db=words_at(data,DB,10)
    db_call,os_call=words_at(data,DB_CALL,2)
    if db[-1]!=0x4e800020 or direct_bl(db_call,DB_CALL)!=DB or direct_bl(os_call,OS_CALL)!=OS:
        raise ValueError('debug and OS entry geometry')
    values=(db_call,db[0],os_call,words_at(data,OS,1)[0])
    return ('#pragma once\n#include "wii_full_os_entry_witness.h"\n'
            'namespace undercover::wii::v433 {\ninline constexpr OsEntryExpectations expected_os{'
            +', '.join(f'0x{v:08x}u' for v in values)+'};\n}\n')

OLD_TERMINAL='''        if(terminal){std::cout<<"V430_DATA_RESULT helpers=6 bss_bytes=963456 return=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'''
NEW_TERMINAL='''        if(terminal){
            std::cout<<"V430_DATA_RESULT helpers=6 bss_bytes=963456 return=1 fallback=0 boot_verified=0"<<std::endl;
            if(!os_entry.begin(cpu)){std::cout<<"V433_OS_INVALID reason="<<os_entry.failure()<<" stage="<<os_entry.stage()<<std::endl;std::_Exit(86);}
            std::cout<<"V433_OS_BEGIN arena_hi_nonzero="<<unsigned(os_entry.arena_hi_nonzero())<<" boot_info_nonzero="<<unsigned(os_entry.boot_info_nonzero())<<std::endl;
            return; // original __start instructions after __init_data
        }'''
OBSERVE='''    static FullOsEntryWitness os_entry(v433::expected_os);
    if(os_entry.stage()){
        if(!os_entry.observe(addr,cpu)){std::cout<<"V433_OS_INVALID reason="<<os_entry.failure()<<" stage="<<os_entry.stage()<<std::endl;std::_Exit(86);}
        if(os_entry.stage()==2u){std::cout<<"V433_OS_DB_ENTRY valid=1"<<std::endl;return;}
        std::cout<<"V433_OS_RESULT db_return=1 debug_stores=4 os_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);
    }
'''
def patch_probe(source:str)->str:
    source=replace_exact(source,'#include "v430_private_data_expectations.h"','#include "v430_private_data_expectations.h"\n#include "v433_private_os_expectations.h"')
    source=replace_exact(source,'    static FullDataWitness data(v430::expected_data);',OBSERVE+'    static FullDataWitness data(v430::expected_data);')
    return replace_exact(source,OLD_TERMINAL,NEW_TERMINAL)

def install(data:bytes,generated:Path,host:Path,digest:str=OWNER_SHA)->None:
    expected=expectations(data,digest)
    counts=dict.fromkeys((DB,OS),0)
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:
            counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('native debug or OS entry missing')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v433_private_os_expectations.h':expected,dest/'wii_full_os_entry_witness.h':(host/'wii_full_os_entry_witness.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination exists')
    probe=patch_probe(data_probe(cache_probe((host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8'))))
    install_data(data,generated,host,digest)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    (dest/'wii_full_start_probe_v419.h').write_text(probe,encoding='utf-8')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V433_OS_ROUTE installed=0');return 1
    print('V433_OS_ROUTE installed=1 db_entry=1 os_entry=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
