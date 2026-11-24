#!/usr/bin/env python3
"""Authenticate original EXI mask helper, four CSR writes and eight handler registrations."""
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v491_exi_poll import expectations as poll_geometry,install as install_poll
from apply_irq_bootstrap_v475 import rewrite
MASK=0x8052693c
SETTER=0x805265f8
ID=0x804efd7c
SITES=(0x804efa40,0x804efa50,0x804efa60,0x804efa6c,0x804efa78,0x804efa84,0x804efa90,0x804efa9c)
WRITES=(0x804efa20,0x804efa24,0x804efa28,0x804efa30)
CALLS=((0x804efa14,MASK),(0x80526958,0x805265ac),(0x80526998,0x805265d4))+tuple((s,SETTER) for s in SITES)+((0x804efaac,ID),)
def expectations(data,digest=OWNER_SHA):
    poll_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS]:raise ValueError('EXI handler call graph')
    if edge(data,0x80526988)[0]!=0x805266e0:raise ValueError('mask alternate path')
    if words_at(data,MASK,32)[-1]!=0x4e800020 or words_at(data,MASK,1)[0]>>26!=37:
        raise ValueError('mask return/prologue')
    handler=words_at(data,SETTER,5)
    if [x>>26 for x in handler[:4]]!=[32,21,31,31] or handler[-1]!=0x4e800020:
        raise ValueError('setter geometry')
    if any(words_at(data,pc,1)[0]>>26!=36 for pc in WRITES):raise ValueError('CSR stores')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    return ('#pragma once\n#include "wii_exi_handler_witness_v500.h"\nnamespace undercover::wii::v500 {\n'
            'inline constexpr ExiHandlerExpectations expected_handlers{{'+','.join(map(fmt,rows))+'}};\n}\n'),sorted({r[0] for r in rows})
POLL_END='        if(exi_poll.stage()==2u){std::cout<<"V491_EXI_POLL_RESULT channels=3 idle=1 mask_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
POLL_NEXT=POLL_END.replace('std::_Exit(0);','if(!exi_handlers.begin(cpu)){std::cout<<"V500_EXI_HANDLER_INVALID reason="<<exi_handlers.failure()<<" stage="<<exi_handlers.stage()<<std::endl;std::_Exit(100);}std::cout<<"V500_EXI_HANDLER_STAGE n=1"<<std::endl;')
PROBE='''    static ExiHandlerWitness exi_handlers(v500::expected_handlers);
    if(exi_handlers.stage()){
        if(!exi_handlers.observe(addr,cpu)){std::cout<<"V500_EXI_HANDLER_INVALID reason="<<exi_handlers.failure()<<" stage="<<exi_handlers.stage()<<std::endl;std::_Exit(100);}
        std::cout<<"V500_EXI_HANDLER_STAGE n="<<exi_handlers.stage()<<std::endl;
        if(exi_handlers.stage()==12u){std::cout<<"V500_EXI_HANDLER_RESULT mask=1 csr=4 handlers=8 id_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
PAIRS=(('#include "wii_exi_poll_witness_v491.h"','#include "wii_exi_poll_witness_v491.h"\n#include "wii_exi_handler_witness_v500.h"'),
('exi_cold_poll_trace.record(false,off,v);return v;','exi_cold_poll_trace.record(false,off,v);exi_mask_trace.record(false,off,v);return v;'),
('exi_cold_poll_trace.record(true,off,value);return true;','exi_cold_poll_trace.record(true,off,value);exi_mask_trace.record(true,off,value);return true;'))
def patch_probe(source):
    source=replace_exact(source,'#include "v491_private_exi_poll_expectations.h"','#include "v491_private_exi_poll_expectations.h"\n#include "v500_private_exi_handler_expectations.h"')
    seam='    static ExiColdPollWitness exi_poll(v491::expected_poll);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),POLL_END,POLL_NEXT)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0)
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('EXI handler trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v500_private_exi_handler_expectations.h':header,
        dest/'wii_exi_handler_witness_v500.h':(host/'wii_exi_handler_witness_v500.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_poll(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';binding=dest/'wii_irq_bank_binding_v481.h'
    new=patch_probe(probe.read_text(encoding='utf-8'));bound=rewrite(binding.read_text(encoding='utf-8'),PAIRS)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8');binding.write_text(bound,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V500_EXI_HANDLER_ROUTE installed=0');return 1
    print('V500_EXI_HANDLER_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
