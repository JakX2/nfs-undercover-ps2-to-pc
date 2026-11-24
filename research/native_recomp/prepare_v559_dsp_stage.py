#!/usr/bin/env python3
"""Authenticate DSP staging through the original flush syscall entry, not its execution."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v556_audio_reset import expectations as audio_geometry,install as install_audio
from make_start_to_dsp_stage_v63 import EDGES,GETHI,FLUSH,MICROCODE
from make_start_to_si_sampling_v58 import data_at
SC=FLUSH+40
def expectations(data,digest=OWNER_SHA):
    audio_geometry(data,digest)
    rows=[edge(data,s) for s,_ in EDGES]
    if len(rows)!=4 or [r[0] for r in rows]!=[p for _,p in EDGES] or words_at(data,GETHI+4,1)!=(0x4e800020,) or words_at(data,SC,2)!=(0x44000002,0x4e800020):
        raise ValueError('DSP staging geometry')
    image=data_at(data,MICROCODE,128)
    if len(image)!=128:raise ValueError('DSP image geometry')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_dsp_stage_witness_v559.h"\nnamespace undercover::wii::v559 {\n'
            'inline constexpr DspStageExpectations expected_stage{{'+','.join(map(fmt,rows))+'},{'+
            ','.join(str(v) for v in image)+'},0x44000002u};\n}\n')
    return header,sorted({r[0] for r in rows})
AUDIO_END='        if(audio_reset.stage()==9u){std::cout<<"V556_AUDIO_RESULT rmw=6 waits=5 reset_return=1 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
AUDIO_NEXT=AUDIO_END.replace('std::_Exit(0);','if(!dsp_stage.begin(cpu)){std::cout<<"V559_DSP_STAGE_INVALID reason="<<dsp_stage.failure()<<" stage="<<dsp_stage.stage()<<std::endl;std::_Exit(112);}std::cout<<"V559_DSP_STAGE n=1"<<std::endl;')
PROBE='''    static DspStageWitness dsp_stage(v559::expected_stage);
    if(dsp_stage.stage()){
        const auto before=dsp_stage.stage();
        if(!dsp_stage.observe(addr,cpu)){std::cout<<"V559_DSP_STAGE_INVALID reason="<<dsp_stage.failure()<<" stage="<<dsp_stage.stage()<<std::endl;std::_Exit(112);}
        if(dsp_stage.stage()!=before)std::cout<<"V559_DSP_STAGE n="<<dsp_stage.stage()<<std::endl;
        if(dsp_stage.stage()==6u){std::cout<<"V559_DSP_STAGE_RESULT backup=1 image=128 flush=4 sc_entry=1 sc_executed=0 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}
        return;
    }
'''
def patch_probe(source):
    source=replace_exact(source,'#include "v556_private_audio_expectations.h"','#include "v556_private_audio_expectations.h"\n#include "v559_private_dsp_stage_expectations.h"')
    seam='    static AudioResetWitness audio_reset(v556::expected_audio);'
    return replace_exact(replace_exact(source,seam,PROBE+seam),AUDIO_END,AUDIO_NEXT)
def patch_label(source):
    pattern=re.compile(r'(?mi)^loc_805222E8: ;\n    // 0x805222E8: 44000002\n')
    if len(pattern.findall(source))!=1 or 'V559 pre-SC staging checkpoint' in source:raise ValueError('SC label')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x805222E8, ctx); // V559 pre-SC staging checkpoint\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets=expectations(data,digest);counts=dict.fromkeys(targets,0);labels=[]
    for shard in generated.glob('output_*.cpp'):
        if shard.is_symlink():raise ValueError('symlink')
        source=shard.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=source.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_805222E8: ;$',source):patch_label(source);labels.append(shard)
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('DSP trace coverage')
    dest=generated/'nWiiRuntime/include/undercover';files={dest/'v559_private_dsp_stage_expectations.h':header,
        dest/'wii_dsp_stage_witness_v559.h':(host/'wii_dsp_stage_witness_v559.h').read_text(encoding='utf-8')}
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_audio(data,generated,host,digest)
    p=dest/'wii_full_start_probe_v419.h';files[p]=patch_probe(p.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    shard=labels[0];shard.write_text(patch_label(shard.read_text(encoding='utf-8')),encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError):
        print('V559_DSP_ROUTE installed=0');return 1
    print('V559_DSP_ROUTE installed=1 read_only=1 sc_executed=0');return 0
if __name__=='__main__':raise SystemExit(main())
