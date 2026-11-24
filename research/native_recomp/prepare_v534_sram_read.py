#!/usr/bin/env python3
"""Private original SRAM read-only DMA and exact OSInit continuation."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v529_si_discovery import expectations as discovery_geometry,install as install_discovery
from make_start_to_sram_return_v60 import EDGES,STOP
CALLS=EDGES[:-1]
def expectations(data,digest=OWNER_SHA):
    discovery_geometry(data,digest)
    rows=[edge(data,s) for s,_ in CALLS]
    if len(rows)!=12 or [x[0] for x in rows]!=[p for _,p in CALLS] or edge(data,EDGES[-1][0])[0]!=EDGES[-1][1]:
        raise ValueError('SRAM call geometry')
    w=words_at(data,STOP,1)[0]
    if not w:raise ValueError('SRAM return instruction')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_sram_read_witness_v534.h"\nnamespace undercover::wii::v534 {\n'
            'inline constexpr SramReadExpectations expected_sram{'+fmt(rows[0])+',{'
            +','.join(map(fmt,rows[1:]))+'},'+f'0x{w:08x}u'+'};\n}\n')
    return header,sorted({x[0] for x in rows}),w
DISC_END='        if(si_discovery.stage()==13u){std::cout<<"V529_SI_DISCOVERY_RESULT type_calls=4 immediate=1 queued=3 completed=1 norep=1 irq=1 sram_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
DISC_NEXT=DISC_END.replace('std::_Exit(0);','if(!sram_read.begin(cpu,ExiTickBinding::active()&&ExiDiConfigBinding::active())){std::cout<<"V534_SRAM_INVALID reason="<<sram_read.failure()<<" stage="<<sram_read.stage()<<std::endl;std::_Exit(108);}std::cout<<"V534_SRAM_STAGE n=1"<<std::endl;')
PROBE='''    static SramReadWitness sram_read(v534::expected_sram);
    if(sram_read.stage()){
        const auto before=sram_read.stage();
        if(!sram_read.observe(addr,cpu)){std::cout<<"V534_SRAM_INVALID reason="<<sram_read.failure()<<" stage="<<sram_read.stage()<<" completed="<<sram_completion.count()<<std::endl;std::_Exit(108);}
        if(sram_read.stage()!=before)std::cout<<"V534_SRAM_STAGE n="<<sram_read.stage()<<std::endl;
        if(sram_read.stage()==13u){std::cout<<"V534_SRAM_RESULT command=1 dma=1 bytes=64 invalidations=2 config_unlock=2 returned=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v529_private_si_discovery_expectations.h"','#include "v529_private_si_discovery_expectations.h"\n#include "v534_private_sram_expectations.h"')
    seam='    static SiDiscoveryWitness si_discovery(v529::expected_discovery);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),DISC_END,DISC_NEXT)
def patch_scheduler(source):
    source=replace_exact(source,'#include "wii_exi_id_witness_v504.h"','#include "wii_exi_id_witness_v504.h"\n#include "wii_sram_read_witness_v534.h"')
    return replace_exact(source,'        exi_id_completion.record(*req,ctl_.read(req->channel,16));','        exi_id_completion.record(*req,ctl_.read(req->channel,16));\n        sram_completion.record(*req,ctl_,mx_);')
def patch_label(source,word):
    pattern=re.compile(r'(?mi)^loc_805208D0: ;\n    // 0x805208D0: '+f'{word:08X}'+r'\n')
    if len(pattern.findall(source))!=1 or 'V534 original SRAM return' in source:raise ValueError('return label')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x805208D0, ctx); // V534 original SRAM return\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,word=expectations(data,digest);counts=dict.fromkeys(targets,0);labels=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_805208D0: ;$',source):patch_label(source,word);labels.append(shard)
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('SRAM trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v534_private_sram_expectations.h':header,
        dest/'wii_sram_read_witness_v534.h':(host/'wii_sram_read_witness_v534.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_discovery(data,generated,host,digest)
    for name,fn in (('wii_full_start_probe_v419.h',patch_probe),('wii_exi_endpoint_scheduler_v495.h',patch_scheduler)):
        p=dest/name;files[p]=fn(p.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    shard=labels[0];shard.write_text(patch_label(shard.read_text(encoding='utf-8'),word),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V534_SRAM_ROUTE installed=0');return 1
    print('V534_SRAM_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
