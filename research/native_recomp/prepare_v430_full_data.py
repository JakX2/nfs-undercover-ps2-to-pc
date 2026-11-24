#!/usr/bin/env python3
"""Extend the private full-image cache witness to genuine __init_data return."""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import struct
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from prepare_v428_full_cache import expectations as cache_expectations,install as install_cache,patch_probe as cache_probe

TABLE=0x80006420;DATA=0x80004238;RETURN=0x80004058
SET=0x8000443c;FILL=0x80004388;COPY=0x80004338;FLUSH=0x80004304
CALLS=((DATA+72,COPY),(DATA+84,FLUSH),(DATA+128,SET),(SET+20,FILL))
COUNTS=((DATA,42),(SET,12),(FILL,45),(COPY,20),(FLUSH,13))

def expectations(data:bytes,digest:str=OWNER_SHA)->tuple[str,set[int],int]:
    cache_expectations(data,digest)
    for pc,n in COUNTS:
        if words_at(data,pc,n)[-1]!=0x4e800020:raise ValueError('data return geometry')
    for site,target in CALLS:
        if direct_bl(words_at(data,site,1)[0],site)!=target:raise ValueError('data call geometry')
    table=words_at(data,TABLE,44)
    for i in range(11):
        a,b,n=table[3*i:3*i+3]
        if a!=b or not 0<n<=0x1000000 or not 0x80000000<=a<a+n<=0x81800000:raise ValueError('copy table geometry')
    if table[35] or table[42] or table[43]:raise ValueError('table terminator')
    zero=[tuple(table[36+2*i:38+2*i]) for i in range(3)]
    if [n for _,n in zero]!=[950236,13164,56]:raise ValueError('zero table lengths')
    for i,(a,n) in enumerate(zero):
        if not 0x80000000<a<a+n<0x81800000 or (i and zero[i-1][0]+zero[i-1][1]>=a):raise ValueError('zero table range')
    def edge(site,target):return f'CacheEdge{{0x{target:08x}u,0x{site+4:08x}u,0x{words_at(data,site,1)[0]:08x}u,0x{words_at(data,target,1)[0]:08x}u}}'
    word=words_at(data,RETURN,1)[0]
    header=('#pragma once\n#include "wii_full_data_witness.h"\nnamespace undercover::wii::v430 {\n'
            'inline constexpr DataExpectations expected_data{{'+', '.join(f'0x{w:08x}u' for w in table)+'},{\n'+
            ',\n'.join(f'DataRange{{0x{a:08x}u,{n}u}}' for a,n in zero)+'\n},'+edge(*CALLS[2])+','+edge(*CALLS[3])+f',0x{word:08x}u}};\n}}\n')
    return header,{SET,FILL},word

OLD_COMPLETE='''            std::cout<<"V428_CACHE_RESULT cache=1 handler=1 data_entry=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);'''
NEW_COMPLETE='''            if(!data.begin(cpu)) { std::cout<<"V430_DATA_INVALID reason="<<data.failure()<<" calls=0"<<std::endl;std::_Exit(85); }
            std::cout<<"V430_DATA_BEGIN before_nonzero="<<data.before_nonzero()<<std::endl;
            return; // original __init_data executes unmodified'''
DATA_OBSERVE='''    static FullDataWitness data(v430::expected_data);
    if(cache.stage()==4u){
        const bool terminal=addr==0x80004058u;
        const bool valid=terminal?data.finish(cpu):data.observe(addr,cpu);
        if(!valid){std::cout<<"V430_DATA_INVALID reason="<<data.failure()<<" calls="<<data.stage()<<std::endl;std::_Exit(85);}
        if(terminal){std::cout<<"V430_DATA_RESULT helpers=6 bss_bytes=963456 return=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        std::cout<<"V430_DATA_HELPER n="<<data.stage()<<" valid=1"<<std::endl;
        return;
    }
'''
def patch_probe(source:str)->str:
    source=replace_exact(source,'#include "v428_private_cache_expectations.h"','#include "v428_private_cache_expectations.h"\n#include "v430_private_data_expectations.h"')
    source=replace_exact(source,'    if(hardware.stage()==6u){',DATA_OBSERVE+'    if(hardware.stage()==6u){')
    return replace_exact(source,OLD_COMPLETE,NEW_COMPLETE)

def return_seam(source:str,word:int)->str:
    # Exact original instruction label and word. The trace occurs immediately
    # before the next guest instruction, never replacing that instruction.
    pat=re.compile(r'(?m)^loc_80004058: ;\n    // 0x80004058: '+f'{word:08X}'+r'\n',re.I)
    hits=list(pat.finditer(source))
    if len(hits)!=1 or 'V430 original data return' in source:raise ValueError('return seam')
    m=hits[0];insertion='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80004058, ctx); // V430 original data return\n'
    out=source[:m.end()]+insertion+source[m.end():]
    if out.replace(insertion,'',1)!=source:raise ValueError('return patch reversibility')
    return out

def install(data:bytes,generated:Path,host:Path,digest:str=OWNER_SHA)->None:
    expected,targets,word=expectations(data,digest)
    counts=dict.fromkeys(targets,0);shards=[]
    for shard in generated.glob('output_*.cpp'):
        source=shard.read_text(encoding='utf-8')
        for pc in counts:
            counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80004058: ;$',source):shards.append((shard,source))
    if any(n!=1 for n in counts.values()) or len(shards)!=1:raise ValueError('native entry/return missing')
    shard,source=shards[0]
    if shard.is_symlink():raise ValueError('symlink')
    updated=return_seam(source,word)
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v430_private_data_expectations.h':expected,dest/'wii_full_data_witness.h':(host/'wii_full_data_witness.h').read_text(encoding='utf-8')}
    if any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination exists')
    probe=patch_probe(cache_probe((host/'wii_full_hardware_probe_v425.h').read_text(encoding='utf-8')))
    install_cache(data,generated,host,digest)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    (dest/'wii_full_start_probe_v419.h').write_text(probe,encoding='utf-8');shard.write_text(updated,encoding='utf-8')

def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V430_DATA_ROUTE installed=0');return 1
    print('V430_DATA_ROUTE installed=1 helpers=6 bss_bytes=963456 original_return=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
