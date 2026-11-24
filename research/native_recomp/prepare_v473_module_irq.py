#!/usr/bin/env python3
"""Compose the original module and IRQ table setup after V470."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v470_alarm_startup import expectations as alarm_geometry,install as install_alarm
MODULE=0x80526d30
IRQ=0x8052661c
STOP=0x8052664c
CALLS=((0x805208b4,MODULE),(0x805208b8,IRQ),(0x80526648,0x8000443c),(0x80004450,0x80004388))
ENDS=(MODULE+24,0x80004388+0xb4,0x80004388+0xe4)
def expectations(data,digest=OWNER_SHA):
    alarm_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS]:raise ValueError('IRQ edges')
    if any(words_at(data,end-4,1)[0]!=0x4e800020 for end in ENDS):raise ValueError('IRQ returns')
    stop=words_at(data,STOP,1)[0]
    fmt=lambda row:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in row)+'}'
    header=('#pragma once\n#include "wii_module_irq_witness_v473.h"\nnamespace undercover::wii::v473 {\n'
            'inline constexpr ModuleIrqExpectations expected_irq{{'+','.join(map(fmt,rows))+'},'+f'0x{stop:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),stop

ALARM_END='        if(alarm.stage()==5u){std::cout<<"V470_ALARM_RESULT dispatch=1 queues=1 module_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
ALARM_NEXT=ALARM_END.replace('std::_Exit(0);','if(!irq.begin(cpu)){std::cout<<"V473_IRQ_INVALID reason="<<irq.failure()<<" stage="<<irq.stage()<<std::endl;std::_Exit(94);}std::cout<<"V473_IRQ_STAGE n=1"<<std::endl;')
IRQ_PROBE='''    static ModuleIrqWitness irq(v473::expected_irq);
    if(irq.stage()){
        if(!irq.observe(addr,cpu)){std::cout<<"V473_IRQ_INVALID reason="<<irq.failure()<<" stage="<<irq.stage()<<std::endl;std::_Exit(94);}
        std::cout<<"V473_IRQ_STAGE n="<<irq.stage()<<std::endl;
        if(irq.stage()==5u){std::cout<<"V473_IRQ_RESULT module=1 table=128 pointer=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v470_private_alarm_expectations.h"','#include "v470_private_alarm_expectations.h"\n#include "v473_private_irq_expectations.h"')
    seam='    static AlarmStartupWitness alarm(v470::expected_alarm);'
    return replace_exact(replace_exact(source,seam,IRQ_PROBE+seam),ALARM_END,ALARM_NEXT)

def return_seam(source,word):
    pat=re.compile(r'(?m)^loc_8052664C: ;\n    // 0x8052664C: '+f'{word:08X}'+r'\n',re.I)
    hits=list(pat.finditer(source))
    if len(hits)!=1 or 'V473 original IRQ memset return' in source:raise ValueError('IRQ return seam')
    at=hits[0].end()
    line='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x8052664C, ctx); // V473 original IRQ memset return\n'
    return source[:at]+line+source[at:]

def install(data,generated,host,digest=OWNER_SHA):
    header,targets,stop=expectations(data,digest)
    counts=dict.fromkeys(targets,0);shards=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_8052664C: ;$',source):shards.append(shard)
    if any(n!=1 for n in counts.values()) or len(shards)!=1:raise ValueError('IRQ trace coverage')
    shard=shards[0]
    return_seam(shard.read_text(encoding='utf-8'),stop)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v473_private_irq_expectations.h':header,
           dest/'wii_module_irq_witness_v473.h':(host/'wii_module_irq_witness_v473.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_alarm(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';new=patch_probe(probe.read_text(encoding='utf-8'))
    source=return_seam(shard.read_text(encoding='utf-8'),stop)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8');shard.write_text(source,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V473_IRQ_ROUTE installed=0');return 1
    print('V473_IRQ_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
