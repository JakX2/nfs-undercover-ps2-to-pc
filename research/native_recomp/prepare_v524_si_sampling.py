#!/usr/bin/env python3
"""Private original SI clock, polling and IRQ registration continuation."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v520_si_entry import expectations as entry_geometry,install as install_entry
from make_start_to_si_sampling_v58 import data_at,RATE_END,XY_END,TV_END
from apply_vi_clock_v522 import apply as install_vi
CALLS=((0x805320d0,0x80532d6c),(0x80532da8,0x80536bf8),(0x80532e1c,0x8053238c),
       (0x805320fc,0x805265f8),(0x80532104,0x805269bc),(0x8053210c,0x80532aa8))
def expectations(data,digest=OWNER_SHA):
    entry_geometry(data,digest)
    rows=[edge(data,s) for s,_ in CALLS]
    if [x[0] for x in rows]!=[p for _,p in CALLS] or any(words_at(data,hi-4,1)[0]!=0x4e800020 for hi in (RATE_END,XY_END,TV_END)):
        raise ValueError('SI sample geometry')
    w=struct.unpack('>I',data_at(data,0x80619a88,4))[0]
    if (w>>16)>511:raise ValueError('SI sample range')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_si_sampling_witness_v524.h"\nnamespace undercover::wii::v524 {\n'
            'inline constexpr SiSamplingExpectations expected_sampling{'+','.join(map(fmt,rows))+f',0x{w:08x}u'+'};\n}\n')
    return header,sorted({x[0] for x in rows})
ENTRY_END='        if(si_entry.stage()==6u){std::cout<<"V520_SI_ENTRY_RESULT exi_return=1 version_tails=2 slots=4 rate_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
ENTRY_NEXT=ENTRY_END.replace('std::_Exit(0);','const auto clock=ViClockBinding::selected();if(!si_sample.begin(cpu,SiBinding::active()&&SiTickBinding::active()&&clock.has_value(),clock.value_or(2))){std::cout<<"V524_SI_SAMPLE_INVALID reason="<<si_sample.failure()<<" stage="<<si_sample.stage()<<std::endl;std::_Exit(106);}std::cout<<"V524_SI_SAMPLE_STAGE n=1"<<std::endl;')
PROBE='''    static SiSamplingWitness si_sample(v524::expected_sampling);
    if(si_sample.stage()){
        const auto before=si_sample.stage();
        if(!si_sample.observe(addr,cpu)){std::cout<<"V524_SI_SAMPLE_INVALID reason="<<si_sample.failure()<<" stage="<<si_sample.stage()<<std::endl;std::_Exit(106);}
        if(si_sample.stage()!=before)std::cout<<"V524_SI_SAMPLE_STAGE n="<<si_sample.stage()<<std::endl;
        if(si_sample.stage()==6u){std::cout<<"V524_SI_SAMPLE_RESULT vi=1 poll=1 clear=1 irq=1 type_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v520_private_si_entry_expectations.h"','#include "v520_private_si_entry_expectations.h"\n#include "v524_private_si_sampling_expectations.h"\n#include "wii_si_profile_v518.h"\n#include "wii_vi_clock_v522.h"')
    seam='    static SiEntryWitness si_entry(v520::expected_si_entry);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),ENTRY_END,ENTRY_NEXT)
def patch_si(source):
    source=replace_exact(source,'#include "wii_si_controller_v511.h"','#include "wii_si_controller_v511.h"\n#include "wii_si_sampling_witness_v524.h"')
    source=replace_exact(source,'        return active_->controller_.read(*off);','        const auto value=active_->controller_.read(*off);si_sampling_trace.si(false,*off,value);return value;')
    return replace_exact(source,'        active_->controller_.write(*off,value);return true;','        active_->controller_.write(*off,value);si_sampling_trace.si(true,*off,value);return true;')
def patch_vi(source):
    source=replace_exact(source,'#include <stdexcept>','#include <stdexcept>\n#include "wii_si_sampling_witness_v524.h"')
    source=replace_exact(source,'        return active_->clock_;','        const auto value=active_->clock_;si_sampling_trace.vi(false,value);return value;')
    return replace_exact(source,'        active_->clock_=value;return true;','        active_->clock_=value;si_sampling_trace.vi(true,value);return true;')
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('SI sampling trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v524_private_si_sampling_expectations.h':header,
        dest/'wii_si_sampling_witness_v524.h':(host/'wii_si_sampling_witness_v524.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_entry(data,generated,host,digest);install_vi(generated,host)
    for name,fn in (('wii_full_start_probe_v419.h',patch_probe),('wii_si_binding_v512.h',patch_si),('wii_vi_clock_v522.h',patch_vi)):
        p=dest/name;files[p]=fn(p.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V524_SI_SAMPLE_ROUTE installed=0');return 1
    print('V524_SI_SAMPLE_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
