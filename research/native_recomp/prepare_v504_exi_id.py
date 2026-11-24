#!/usr/bin/env python3
"""Private full-image uncached ID continuation; require actual scheduled device responses."""
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v500_exi_handlers import expectations as handler_geometry,install as install_handlers
from apply_exi_tick_v497 import runtime as install_tick
from apply_exi_profile_v501 import apply as install_profile
from make_start_to_exi_transaction_v56 import EDGES,RANGES
CALLS=((0x804efaac,0x804efd7c),(0x804eff00,0x804efb80),(0x804efc54,0x804ee894),
       (0x804eff1c,0x804ef3ec),(0x804eff48,0x804ee984),(0x804eff5c,0x804eed9c),
       (0x804eef58,0x80521008),(0x804eff80,0x804ee984),(0x804eff94,0x804eed9c),
       (0x804eef58,0x80521008),(0x804effa8,0x804ef51c),(0x804effe8,0x804ee894))
RETURN=0x804efab0
def expectations(data,digest=OWNER_SHA):
    handler_geometry(data,digest)
    rows=[edge(data,site) for site,_ in CALLS]
    if [r[0] for r in rows]!=[pc for _,pc in CALLS] or any(edge(data,s)[0]!=t for s,t in EDGES):raise ValueError('ID call graph')
    if any(words_at(data,hi-4,1)[0]!=0x4e800020 for _,hi in RANGES):raise ValueError('ID helper return')
    word=words_at(data,RETURN,1)[0]
    if word>>26!=32:raise ValueError('ID return load')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_exi_id_witness_v504.h"\nnamespace undercover::wii::v504 {\n'
            'inline constexpr ExiIdExpectations expected_id{{'+','.join(map(fmt,rows))+'},'+f'0x{word:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),word
HANDLER_END='        if(exi_handlers.stage()==12u){std::cout<<"V500_EXI_HANDLER_RESULT mask=1 csr=4 handlers=8 id_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
HANDLER_NEXT=HANDLER_END.replace('std::_Exit(0);','if(!exi_id.begin(cpu,ExiTickBinding::active()&&ExiDiConfigBinding::active())){std::cout<<"V504_EXI_ID_INVALID reason="<<exi_id.failure()<<" stage="<<exi_id.stage()<<std::endl;std::_Exit(102);}std::cout<<"V504_EXI_ID_STAGE n=1"<<std::endl;')
PROBE='''    static ExiIdWitness exi_id(v504::expected_id);
    if(exi_id.stage()){
        const auto before=exi_id.stage();
        if(!exi_id.observe(addr,cpu)){std::cout<<"V504_EXI_ID_INVALID reason="<<exi_id.failure()<<" stage="<<exi_id.stage()<<std::endl;std::_Exit(102);}
        if(exi_id.stage()!=before)std::cout<<"V504_EXI_ID_STAGE n="<<exi_id.stage()<<std::endl;
        if(exi_id.stage()==13u){std::cout<<"V504_EXI_ID_RESULT transfers=2 id_copy=1 unlocked=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v500_private_exi_handler_expectations.h"','#include "v500_private_exi_handler_expectations.h"\n#include "v504_private_exi_id_expectations.h"\n#include "wii_exi_profile_v501.h"')
    seam='    static ExiHandlerWitness exi_handlers(v500::expected_handlers);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),HANDLER_END,HANDLER_NEXT)
def patch_label(source,word):
    pattern=re.compile(r'(?mi)^loc_804EFAB0: ;\n    // 0x804EFAB0: '+f'{word:08X}'+r'\n')
    if len(pattern.findall(source))!=1 or 'V504 original ID return' in source:raise ValueError('return label')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x804EFAB0, ctx); // V504 original ID return\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,word=expectations(data,digest);counts=dict.fromkeys(targets,0);labels=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_804EFAB0: ;$',source):labels.append((shard,patch_label(source,word)))
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('ID trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v504_private_exi_id_expectations.h':header,
        dest/'wii_exi_id_witness_v504.h':(host/'wii_exi_id_witness_v504.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_handlers(data,generated,host,digest);install_tick(generated,host);install_profile(generated,host)
    probe=dest/'wii_full_start_probe_v419.h';scheduler=dest/'wii_exi_endpoint_scheduler_v495.h'
    new=patch_probe(probe.read_text(encoding='utf-8'))
    sched=replace_exact(scheduler.read_text(encoding='utf-8'),'#include "wii_exi_mx_device_v494.h"','#include "wii_exi_mx_device_v494.h"\n#include "wii_exi_id_witness_v504.h"')
    sched=replace_exact(sched,'        ++completed_;token_=0;','        exi_id_completion.record(*req,ctl_.read(req->channel,16));\n        ++completed_;token_=0;')
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    probe.write_text(new,encoding='utf-8');scheduler.write_text(sched,encoding='utf-8')
    # Re-read after predecessor installers, which may patch a different
    # label in the same shard.
    shard,_=labels[0];shard.write_text(patch_label(shard.read_text(encoding='utf-8'),word),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V504_EXI_ID_ROUTE installed=0');return 1
    print('V504_EXI_ID_ROUTE installed=1 read_only=1 profile_required=1');return 0
if __name__=='__main__':raise SystemExit(main())
