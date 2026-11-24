#!/usr/bin/env python3
"""Authenticate original cache callsites, extend V425 through cache return."""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v425_full_hardware import hardware_expectations,install as install_hardware,CACHE

ALLOWED={0x804b7920,0x805223bc,0x80522280,0x804b7930,0x804b7938,0x804b7910,0x804b7918,0x804e50b8,0x805230b8}
ERROR=0x805230b8; DATA=0x80004238; DATA_LR=0x80004058
ERROR_CALLS=((0x805230dc,0x805265ac),(0x80523318,0x805265d4))

def expectations(data:bytes,digest:str=OWNER_SHA)->tuple[str,set[int]]:
    hardware_expectations(data,digest)
    cache=words_at(data,CACHE,78);error=words_at(data,ERROR,162)
    if cache[-1]!=0x4e800020 or error[-1]!=0x4e800020:raise ValueError('return geometry')
    def edge(site,target):
        w=words_at(data,site,1)[0]
        if direct_bl(w,site)!=target:raise ValueError('call geometry')
        return f'CacheEdge{{0x{target:08x}u,0x{site+4:08x}u,0x{w:08x}u,0x{words_at(data,target,1)[0]:08x}u}}'
    calls=[(CACHE+4*i,direct_bl(w,CACHE+4*i)) for i,w in enumerate(cache) if w>>26==18 and w&1]
    if len(calls)!=26 or {t for _,t in calls}!=ALLOWED:raise ValueError('cache calls')
    targets=ALLOWED|{t for _,t in ERROR_CALLS}|{DATA}
    return ('#pragma once\n#include "wii_full_cache_witness.h"\nnamespace undercover::wii::v428 {\n'
            'inline constexpr CacheExpectations expected_cache{{\n'+',\n'.join(edge(s,t) for s,t in calls)+'\n},{\n'+
            ',\n'.join(edge(s,t) for s,t in ERROR_CALLS)+'\n},'+edge(DATA_LR-4,DATA)+'};\n}\n'),targets

OLD_COMPLETE='''        std::cout<<"V425_HARDWARE_RESULT entry=1 registers=1 ps=1 fpr=1 cache_entry=1 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);'''
NEW_COMPLETE='''        if(!cache.begin(cpu)) { std::cout<<"V428_CACHE_INVALID reason=1 stage=0 calls=0"<<std::endl;std::_Exit(84); }
        return; // genuine cache body executes in the complete image'''
CACHE_OBSERVE='''    static FullCacheWitness cache(v428::expected_cache);
    if(hardware.stage()==6u){
        const unsigned prior=cache.stage();
        const auto outcome=cache.observe(addr,cpu);
        if(outcome==FullStartResult::Invalid){
            std::cout<<"V428_CACHE_INVALID reason="<<cache.failure()<<" stage="<<cache.stage()<<" calls="<<cache.calls()<<std::endl;std::_Exit(84);
        }
        if(prior!=cache.stage())std::cout<<"V428_CACHE_STAGE n="<<cache.stage()<<" valid=1"<<std::endl;
        if(outcome==FullStartResult::Complete){
            std::cout<<"V428_CACHE_RESULT cache=1 handler=1 data_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);
        }
        return;
    }
'''
def patch_probe(source:str)->str:
    source=replace_exact(source,'#include "v425_private_hardware_expectations.h"','#include "v425_private_hardware_expectations.h"\n#include "v428_private_cache_expectations.h"')
    source=replace_exact(source,'    FullStartResult result;',CACHE_OBSERVE+'    FullStartResult result;')
    return replace_exact(source,OLD_COMPLETE,NEW_COMPLETE)

def install(data:bytes,generated:Path,host:Path,digest:str=OWNER_SHA)->None:
    expected,targets=expectations(data,digest)
    counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:
            counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('missing native entry')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v428_private_cache_expectations.h':expected,dest/'wii_full_cache_witness.h':(host/'wii_full_cache_witness.h').read_text(encoding='utf-8')}
    if any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination exists')
    probe=patch_probe((host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8'))
    install_hardware(data,generated,host,digest)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    (dest/'wii_full_start_probe_v419.h').write_text(probe,encoding='utf-8')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V428_CACHE_ROUTE installed=0');return 1
    print('V428_CACHE_ROUTE installed=1 cap=128 original_calls=26 interpreter_reject=1');return 0
if __name__=='__main__':raise SystemExit(main())
