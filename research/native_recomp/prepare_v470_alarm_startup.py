#!/usr/bin/env python3
"""Prepare a private complete-image alarm continuation, after V466."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import expectations as pack_geometry,install as install_pack,edge

ALARM=0x805210cc
MODULE=0x80526d30
CALLS=((0x805208b0,ALARM),(ALARM+0x10,0x80520eb0),
       (ALARM+0x38,0x80520e9c),(ALARM+0x44,0x80527b4c),(0x805208b4,MODULE))
ENDS=(ALARM+0x58,0x80520e9c+0x14,0x80520eb0+0x10,0x80527b4c+0x88)

def expectations(data,digest=OWNER_SHA):
    pack_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS]:raise ValueError('alarm edges')
    if any(words_at(data,end-4,1)[0]!=0x4e800020 for end in ENDS):raise ValueError('alarm returns')
    fmt=lambda row:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in row)+'}'
    header=('#pragma once\n#include "wii_alarm_startup_witness_v470.h"\nnamespace undercover::wii::v470 {\n'
            'inline constexpr std::array<VectorEdge,5> expected_alarm{'+','.join(map(fmt,rows))+'};\n}\n')
    return header,sorted({r[0] for r in rows})

PACK_END='        if(pack.phase()==4u){std::cout<<"V466_PACK_RESULT vectors=15 syscall=1 alarm_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
PACK_NEXT=PACK_END.replace('std::_Exit(0);','if(!alarm.begin(cpu)){std::cout<<"V470_ALARM_INVALID reason="<<alarm.failure()<<" stage="<<alarm.stage()<<std::endl;std::_Exit(93);}std::cout<<"V470_ALARM_STAGE n=1"<<std::endl;')
ALARM_PROBE='''    static AlarmStartupWitness alarm(v470::expected_alarm);
    if(alarm.stage()){
        if(!alarm.observe(addr,cpu)){std::cout<<"V470_ALARM_INVALID reason="<<alarm.failure()<<" stage="<<alarm.stage()<<std::endl;std::_Exit(93);}
        std::cout<<"V470_ALARM_STAGE n="<<alarm.stage()<<std::endl;
        if(alarm.stage()==5u){std::cout<<"V470_ALARM_RESULT dispatch=1 queues=1 module_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v466_private_pack_expectations.h"','#include "v466_private_pack_expectations.h"\n#include "v470_private_alarm_expectations.h"')
    seam='    static ExceptionPackRoute pack(v466::expected_pack);'
    return replace_exact(replace_exact(source,seam,ALARM_PROBE+seam),PACK_END,PACK_NEXT)

def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest)
    counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('alarm trace coverage')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v470_private_alarm_expectations.h':header,
           dest/'wii_alarm_startup_witness_v470.h':(host/'wii_alarm_startup_witness_v470.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_pack(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V470_ALARM_ROUTE installed=0');return 1
    print('V470_ALARM_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
