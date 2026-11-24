#!/usr/bin/env python3
"""Authenticate original default-thread init including the indirect callback."""
import argparse
from pathlib import Path
import struct
import re
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v534_sram_read import expectations as sram_geometry,install as install_sram
from make_start_to_thread_return_v61 import EDGES,RANGES,CALLBACK,CALLBACK_PTR,STOP
from make_start_to_si_sampling_v58 import data_at
INDIRECT=0x805291dc
def expectations(data,digest=OWNER_SHA):
    sram_geometry(data,digest)
    rows=[edge(data,s) for s,_ in EDGES]
    if [r[0] for r in rows]!=[p for _,p in EDGES] or any(words_at(data,hi-4,1)[0]!=0x4e800020 for _,hi in RANGES):
        raise ValueError('thread call geometry')
    w=words_at(data,INDIRECT,1)[0]
    if w>>26!=19 or (w>>1)&1023!=528 or not w&1 or struct.unpack('>I',data_at(data,CALLBACK_PTR,4))[0]!=CALLBACK:
        raise ValueError('thread callback geometry')
    rows.insert(3,(CALLBACK,INDIRECT+4,w,words_at(data,CALLBACK,1)[0]))
    ret=words_at(data,STOP,1)[0]
    if not ret:raise ValueError('thread return')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_thread_init_witness_v549.h"\nnamespace undercover::wii::v549 {\n'
            'inline constexpr ThreadInitExpectations expected_thread{'+','.join(map(fmt,rows))+f',0x{ret:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),ret
SRAM_END='        if(sram_read.stage()==13u){std::cout<<"V534_SRAM_RESULT command=1 dma=1 bytes=64 invalidations=2 config_unlock=2 returned=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
SRAM_NEXT=SRAM_END.replace('std::_Exit(0);','if(!thread_init.begin(cpu)){std::cout<<"V549_THREAD_INVALID reason="<<thread_init.failure()<<" stage="<<thread_init.stage()<<std::endl;std::_Exit(110);}std::cout<<"V549_THREAD_STAGE n=1"<<std::endl;')
PROBE='''    static ThreadInitWitness thread_init(v549::expected_thread);
    if(thread_init.stage()){
        const auto before=thread_init.stage();
        if(!thread_init.observe(addr,cpu)){std::cout<<"V549_THREAD_INVALID reason="<<thread_init.failure()<<" stage="<<thread_init.stage()<<std::endl;std::_Exit(110);}
        if(thread_init.stage()!=before)std::cout<<"V549_THREAD_STAGE n="<<thread_init.stage()<<std::endl;
        if(thread_init.stage()==8u){std::cout<<"V549_THREAD_RESULT context=1 callback=1 stack=1 idle=1 returned=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v534_private_sram_expectations.h"','#include "v534_private_sram_expectations.h"\n#include "v549_private_thread_expectations.h"')
    seam='    static SramReadWitness sram_read(v534::expected_sram);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),SRAM_END,SRAM_NEXT)
def patch_label(source,word):
    pattern=re.compile(r'(?mi)^loc_805208D4: ;\n    // 0x805208D4: '+f'{word:08X}'+r'\n')
    if len(pattern.findall(source))!=1 or 'V549 original thread return' in source:raise ValueError('return label')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x805208D4, ctx); // V549 original thread return\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,word=expectations(data,digest);counts=dict.fromkeys(targets,0);labels=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_805208D4: ;$',source):patch_label(source,word);labels.append(shard)
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('thread trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v549_private_thread_expectations.h':header,
        dest/'wii_thread_init_witness_v549.h':(host/'wii_thread_init_witness_v549.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_sram(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    shard=labels[0];shard.write_text(patch_label(shard.read_text(encoding='utf-8'),word),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V549_THREAD_ROUTE installed=0');return 1
    print('V549_THREAD_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
