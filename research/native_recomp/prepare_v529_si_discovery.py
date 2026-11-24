#!/usr/bin/env python3
"""Private original SIInit cold return, actual type completion, and SRAM entry."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v524_si_sampling import expectations as sample_geometry,install as install_sample
from make_start_to_si_return_v59 import EDGES,RANGES,TYPE,TRANSFER,START_TRANSFER,STOP
from make_start_to_sram_return_v60 import SRAM
CALLS=tuple((0x8053210c+8*i,TYPE) for i in range(4))+((0x80532c34,TRANSFER),(0x80532798,START_TRANSFER),(STOP,SRAM))
def expectations(data,digest=OWNER_SHA):
    sample_geometry(data,digest)
    rows=[edge(data,s) for s,_ in CALLS]
    if [x[0] for x in rows]!=[p for _,p in CALLS] or any(edge(data,s)[0]!=p for s,p in EDGES):
        raise ValueError('SI discovery geometry')
    if any(words_at(data,hi-4,1)[0]!=0x4e800020 for _,hi in RANGES):raise ValueError('SI discovery return')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_si_discovery_witness_v529.h"\nnamespace undercover::wii::v529 {\n'
            'inline constexpr SiDiscoveryExpectations expected_discovery{{'+','.join(map(fmt,rows[:4]))+'},'
            +','.join(map(fmt,rows[4:]))+'};\n}\n')
    return header,sorted({x[0] for x in rows})
SAMPLE_END='        if(si_sample.stage()==6u){std::cout<<"V524_SI_SAMPLE_RESULT vi=1 poll=1 clear=1 irq=1 type_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
SAMPLE_NEXT=SAMPLE_END.replace('std::_Exit(0);','if(!si_discovery.begin(cpu,SiBinding::active()&&SiTickBinding::active())){std::cout<<"V529_SI_DISCOVERY_INVALID reason="<<si_discovery.failure()<<" stage="<<si_discovery.stage()<<std::endl;std::_Exit(107);}std::cout<<"V529_SI_DISCOVERY_STAGE n=1"<<std::endl;')
PROBE='''    static SiDiscoveryWitness si_discovery(v529::expected_discovery);
    if(si_discovery.stage()){
        const auto before=si_discovery.stage();
        if(!si_discovery.observe(addr,cpu)){std::cout<<"V529_SI_DISCOVERY_INVALID reason="<<si_discovery.failure()<<" stage="<<si_discovery.stage()<<" mmio="<<si_discovery_trace.stage()<<std::endl;std::_Exit(107);}
        if(si_discovery.stage()!=before)std::cout<<"V529_SI_DISCOVERY_STAGE n="<<si_discovery.stage()<<std::endl;
        if(si_discovery.stage()==13u){std::cout<<"V529_SI_DISCOVERY_RESULT type_calls=4 immediate=1 queued=3 completed=1 norep=1 irq=1 sram_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v524_private_si_sampling_expectations.h"','#include "v524_private_si_sampling_expectations.h"\n#include "v529_private_si_discovery_expectations.h"')
    seam='    static SiSamplingWitness si_sample(v524::expected_sampling);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),SAMPLE_END,SAMPLE_NEXT)
def patch_si(source):
    source=replace_exact(source,'#include "wii_si_sampling_witness_v524.h"','#include "wii_si_sampling_witness_v524.h"\n#include "wii_si_discovery_witness_v529.h"')
    source=replace_exact(source,'si_sampling_trace.si(false,*off,value);','si_sampling_trace.si(false,*off,value);si_discovery_trace.mmio(false,*off,value);')
    return replace_exact(source,'si_sampling_trace.si(true,*off,value);','si_sampling_trace.si(true,*off,value);si_discovery_trace.mmio(true,*off,value);')
def patch_scheduler(source):
    source=replace_exact(source,'#include "wii_si_controller_v511.h"','#include "wii_si_controller_v511.h"\n#include "wii_si_discovery_witness_v529.h"')
    return replace_exact(source,'        ++completed_;token_=0;','        si_discovery_trace.completion(*q,ctl_,tick);\n        ++completed_;token_=0;')
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('SI discovery trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v529_private_si_discovery_expectations.h':header,
        dest/'wii_si_discovery_witness_v529.h':(host/'wii_si_discovery_witness_v529.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_sample(data,generated,host,digest)
    for name,fn in (('wii_full_start_probe_v419.h',patch_probe),('wii_si_binding_v512.h',patch_si),('wii_si_type_scheduler_v514.h',patch_scheduler)):
        p=dest/name;files[p]=fn(p.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V529_SI_DISCOVERY_ROUTE installed=0');return 1
    print('V529_SI_DISCOVERY_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
