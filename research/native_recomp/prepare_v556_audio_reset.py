#!/usr/bin/env python3
"""Authenticate original audio clock reset and compose its read-only witness."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v549_thread_init import expectations as thread_geometry,install as install_thread
from make_start_to_audio_reset_v62 import EDGES,RANGES,AUDIO,STOP
from apply_audio_acr_v537 import apply as install_acr
def expectations(data,digest=OWNER_SHA):
    thread_geometry(data,digest)
    rows=[edge(data,s) for s,_ in EDGES]
    if [x[0] for x in rows]!=[p for _,p in EDGES] or any(words_at(data,hi-4,1)[0]!=0x4e800020 for lo,hi in RANGES if lo!=AUDIO):
        raise ValueError('audio reset geometry')
    ret=words_at(data,STOP,1)[0]
    if not ret:raise ValueError('audio return')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_audio_reset_witness_v556.h"\nnamespace undercover::wii::v556 {\n'
            'inline constexpr AudioResetExpectations expected_audio{'+','.join(map(fmt,rows[:2]))+',{{'+
            ','.join(map(fmt,rows[2:]))+'}},'+f'0x{ret:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),ret
THREAD_END='        if(thread_init.stage()==8u){std::cout<<"V549_THREAD_RESULT context=1 callback=1 stack=1 idle=1 returned=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
THREAD_NEXT=THREAD_END.replace('std::_Exit(0);','if(!audio_reset.begin(cpu,AudioAcrBinding::active())){std::cout<<"V556_AUDIO_INVALID reason="<<audio_reset.failure()<<" stage="<<audio_reset.stage()<<std::endl;std::_Exit(111);}std::cout<<"V556_AUDIO_STAGE n=1"<<std::endl;')
PROBE='''    static AudioResetWitness audio_reset(v556::expected_audio);
    if(audio_reset.stage()){
        const auto before=audio_reset.stage();
        if(!audio_reset.observe(addr,cpu)){std::cout<<"V556_AUDIO_INVALID reason="<<audio_reset.failure()<<" stage="<<audio_reset.stage()<<std::endl;std::_Exit(111);}
        if(audio_reset.stage()!=before)std::cout<<"V556_AUDIO_STAGE n="<<audio_reset.stage()<<std::endl;
        if(audio_reset.stage()==9u){std::cout<<"V556_AUDIO_RESULT rmw=6 waits=5 reset_return=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v549_private_thread_expectations.h"','#include "v549_private_thread_expectations.h"\n#include "v556_private_audio_expectations.h"\n#include "wii_audio_acr_v537.h"')
    seam='    static ThreadInitWitness thread_init(v549::expected_thread);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),THREAD_END,THREAD_NEXT)
def patch_acr(source):
    source=replace_exact(source,'#include <stdexcept>','#include <stdexcept>\n#include "wii_audio_reset_trace_v556.h"')
    source=replace_exact(source,'        return i?std::optional<uint32_t>(active_->values_[*i]):std::nullopt;','        if(!i)return std::nullopt;\n        const auto value=active_->values_[*i];audio_reset_trace.record(false,Addresses[*i],value);return value;')
    return replace_exact(source,'        previous=value;return true;','        previous=value;audio_reset_trace.record(true,Addresses[*i],value);return true;')
def patch_label(source,word):
    pattern=re.compile(r'(?mi)^loc_80522010: ;\n    // 0x80522010: '+f'{word:08X}'+r'\n')
    if len(pattern.findall(source))!=1 or 'V556 original audio reset return' in source:raise ValueError('return label')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80522010, ctx); // V556 original audio reset return\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,word=expectations(data,digest);counts=dict.fromkeys(targets,0);labels=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_80522010: ;$',source):patch_label(source,word);labels.append(shard)
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('audio trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={
        dest/'v556_private_audio_expectations.h':header}
    for name in ('wii_audio_reset_trace_v556.h','wii_audio_reset_witness_v556.h'):
        files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_thread(data,generated,host,digest);install_acr(generated,host)
    for name,fn in (('wii_full_start_probe_v419.h',patch_probe),('wii_audio_acr_v537.h',patch_acr)):
        p=dest/name;files[p]=fn(p.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    shard=labels[0];shard.write_text(patch_label(shard.read_text(encoding='utf-8'),word),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V556_AUDIO_ROUTE installed=0');return 1
    print('V556_AUDIO_ROUTE installed=1 read_only=1');return 0
if __name__=='__main__':raise SystemExit(main())
