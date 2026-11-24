#!/usr/bin/env python3
"""Authenticate original absent-card EXIGetID/EXIProbe returns and version entry."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v504_exi_id import expectations as id_geometry,install as install_id,RETURN
from make_start_to_exi_return_v57 import EDGES,EXI_END,PROBE_END,VERSION_POINTER,version_data
CALLS=((0x804efaf8,0x804efd7c),(0x804efb30,0x804efd7c),(0x804efde8,0x804ef09c),
       (0x804ef0e0,0x805265ac),(0x804ef1f4,0x805265d4),(0x804efb5c,0x80521018))
RETURNS=(0x804efafc,0x804efb34)
def expectations(data,digest=OWNER_SHA):
    _,_,first=id_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS] or any(edge(data,s)[0]!=t for s,t in EDGES):raise ValueError('absent call graph')
    if any(words_at(data,pc-4,1)[0]!=0x4e800020 for pc in (EXI_END,PROBE_END)):raise ValueError('EXI return geometry')
    version=struct.unpack('>I',version_data(data))[0]
    words=[words_at(data,pc,1)[0] for pc in RETURNS]
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_exi_absent_witness_v510.h"\nnamespace undercover::wii::v510 {\n'
            'inline constexpr ExiAbsentExpectations expected_absent{{'+','.join(map(fmt,rows[:5]))+'},'+fmt(rows[5])+','
            +f'0x{first:08x}u,{{0x{words[0]:08x}u,0x{words[1]:08x}u}},0x{version:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),dict(zip(RETURNS,words))
ID_END='        if(exi_id.stage()==13u){std::cout<<"V504_EXI_ID_RESULT transfers=2 id_copy=1 unlocked=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
ID_NEXT=ID_END.replace('std::_Exit(0);','if(!exi_absent.begin(cpu)){std::cout<<"V510_EXI_ABSENT_INVALID reason="<<exi_absent.failure()<<" stage="<<exi_absent.stage()<<std::endl;std::_Exit(103);}std::cout<<"V510_EXI_ABSENT_STAGE n=1"<<std::endl;')
PROBE='''    static ExiAbsentWitness exi_absent(v510::expected_absent);
    if(exi_absent.stage()){
        const auto before=exi_absent.stage();
        if(!exi_absent.observe(addr,cpu)){std::cout<<"V510_EXI_ABSENT_INVALID reason="<<exi_absent.failure()<<" stage="<<exi_absent.stage()<<std::endl;std::_Exit(103);}
        if(exi_absent.stage()!=before)std::cout<<"V510_EXI_ABSENT_STAGE n="<<exi_absent.stage()<<std::endl;
        if(exi_absent.stage()==8u){std::cout<<"V510_EXI_ABSENT_RESULT cards=2 absent=1 extra_transfers=0 version_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v504_private_exi_id_expectations.h"','#include "v504_private_exi_id_expectations.h"\n#include "v510_private_exi_absent_expectations.h"')
    seam='    static ExiIdWitness exi_id(v504::expected_id);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),ID_END,ID_NEXT)
def patch_label(source,pc,word):
    pattern=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}'+r': '+f'{word:08X}'+r'\n')
    label=f' // V510 original absent ID return {pc:X}\n'
    if len(pattern.findall(source))!=1 or label in source:raise ValueError('return label')
    return pattern.sub(lambda m:m[0]+f'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x{pc:X}, ctx);'+label,source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,words=expectations(data,digest);counts=dict.fromkeys(targets,0);labels={}
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        for pc,word in words.items():
            if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',source):
                if pc in labels:raise ValueError('duplicate return')
                patch_label(source,pc,word);labels[pc]=shard
    if any(n!=1 for n in counts.values()) or set(labels)!=set(words):raise ValueError('absent trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v510_private_exi_absent_expectations.h':header,
        dest/'wii_exi_absent_witness_v510.h':(host/'wii_exi_absent_witness_v510.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_id(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';scheduler=dest/'wii_exi_endpoint_scheduler_v495.h';binding=dest/'wii_irq_bank_binding_v481.h'
    new=patch_probe(probe.read_text(encoding='utf-8'))
    sched=replace_exact(scheduler.read_text(encoding='utf-8'),'#include "wii_exi_id_witness_v504.h"','#include "wii_exi_id_witness_v504.h"\n#include "wii_exi_absent_witness_v510.h"')
    sched=replace_exact(sched,'        exi_id_completion.record(*req,ctl_.read(req->channel,16));','        exi_id_completion.record(*req,ctl_.read(req->channel,16));\n        exi_absent_trace.completion();')
    bind=replace_exact(binding.read_text(encoding='utf-8'),'#include "wii_exi_handler_witness_v500.h"','#include "wii_exi_handler_witness_v500.h"\n#include "wii_exi_absent_witness_v510.h"')
    bind=replace_exact(bind,'exi_mask_trace.record(false,off,v);return v;','exi_mask_trace.record(false,off,v);exi_absent_trace.mmio(false,off,v);return v;')
    bind=replace_exact(bind,'exi_mask_trace.record(true,off,value);return true;','exi_mask_trace.record(true,off,value);exi_absent_trace.mmio(true,off,value);return true;')
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8');scheduler.write_text(sched,encoding='utf-8');binding.write_text(bind,encoding='utf-8')
    for pc,shard in labels.items():shard.write_text(patch_label(shard.read_text(encoding='utf-8'),pc,words[pc]),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V510_EXI_ABSENT_ROUTE installed=0');return 1
    print('V510_EXI_ABSENT_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
