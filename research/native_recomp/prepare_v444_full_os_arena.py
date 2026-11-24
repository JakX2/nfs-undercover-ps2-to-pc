#!/usr/bin/env python3
"""Prepare a read-only complete-image boot record and MEM1 arena observer."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v439_full_os_hardware import expectations as hw_expectations,install as install_hw
from make_osinit_lowmem_v31 import validate as validate_lowmem
from make_osinit_arena_v32 import validate_os,validate_setter

PREV=0x80520700;MID=0x80520778;STOP=0x80520818
EDGES=((0x805207e8,0x80521d60),(0x80520814,0x80521d48))

def expectations(data,digest=OWNER_SHA):
    hw_expectations(data,digest)
    def block(pc,n):return struct.pack('>'+str(n)+'I',*words_at(data,pc,n))
    validate_lowmem(block(PREV,(MID-PREV)//4))
    validate_os(block(MID,(STOP-MID)//4))
    rows=[]
    for site,target in EDGES:
        validate_setter(block(target,2),target)
        branch=words_at(data,site,1)[0]
        if direct_bl(branch,site)!=target:raise ValueError('arena edge')
        rows.append('ArenaEdge{'+','.join(f'0x{x:08x}u' for x in (target,site+4,branch,words_at(data,target,1)[0]))+'}')
    stop=words_at(data,STOP,1)[0]
    return ('#pragma once\n#include "wii_full_os_arena_witness.h"\nnamespace undercover::wii::v444 {\n'
            'inline constexpr OsArenaExpectations expected_arena{{'+','.join(rows)+'},'+f'0x{stop:08x}u'+'};\n}\n'),stop

OLD='        if(os_hw.stage()==13u){std::cout<<"V439_HW_RESULT exec=1 perf=6 hid4=1 hid0=1 fpscr=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
NEW='''        if(os_hw.stage()==13u){
            std::cout<<"V439_HW_RESULT exec=1 perf=6 hid4=1 hid0=1 fpscr=1 fallback=0 boot_verified=0"<<std::endl;
            if(!os_arena.begin(cpu)){std::cout<<"V444_ARENA_INVALID reason="<<os_arena.failure()<<" stage="<<os_arena.stage()<<std::endl;std::_Exit(89);}
            std::cout<<"V444_ARENA_BEGIN boot_path="<<os_arena.boot_path()<<" direct_low="<<unsigned(os_arena.direct_low())<<std::endl;
        }'''
OBSERVE='''    static FullOsArenaWitness os_arena(v444::expected_arena);
    if(os_arena.active()){
        if(!os_arena.observe(addr,cpu)){std::cout<<"V444_ARENA_INVALID reason="<<os_arena.failure()<<" stage="<<os_arena.stage()<<std::endl;std::_Exit(89);}
        std::cout<<"V444_ARENA_STAGE n="<<os_arena.stage()-1u<<" valid=1"<<std::endl;
        if(os_arena.stage()==4u){std::cout<<"V444_ARENA_RESULT boot_info=1 low_store=1 high_store=1 bounds=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v439_private_hw_expectations.h"','#include "v439_private_hw_expectations.h"\n#include "v444_private_arena_expectations.h"')
    seam='    static FullOsHardwareWitness os_hw(v439::expected_hw);'
    source=replace_exact(source,seam,OBSERVE+seam)
    return replace_exact(source,OLD,NEW)

def return_seam(source,word):
    pat=re.compile(r'(?m)^loc_80520818: ;\n    // 0x80520818: '+f'{word:08X}'+r'\n',re.I)
    hits=list(pat.finditer(source))
    if len(hits)!=1 or 'V444 original arena return' in source:raise ValueError('return seam')
    at=hits[0].end();line='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80520818, ctx); // V444 original arena return\n'
    out=source[:at]+line+source[at:]
    if out.replace(line,'',1)!=source:raise ValueError('roundtrip')
    return out

def install(data,generated,host,digest=OWNER_SHA):
    expected,stop=expectations(data,digest)
    counts=dict.fromkeys(pc for _,pc in EDGES);counts={pc:0 for pc in counts};shards=[]
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80520818: ;$',source):shards.append((shard,source))
    if any(n!=1 for n in counts.values()) or len(shards)!=1:raise ValueError('arena native coverage')
    shard,source=shards[0]
    if shard.is_symlink():raise ValueError('symlink')
    return_seam(source,stop)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v444_private_arena_expectations.h':expected,dest/'wii_full_os_arena_witness.h':(host/'wii_full_os_arena_witness.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_hw(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h'
    updated=patch_probe(probe.read_text(encoding='utf-8'))
    source=return_seam(shard.read_text(encoding='utf-8'),stop)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(updated,encoding='utf-8');shard.write_text(source,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V444_ARENA_ROUTE installed=0');return 1
    print('V444_ARENA_ROUTE installed=1 edges=2 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
