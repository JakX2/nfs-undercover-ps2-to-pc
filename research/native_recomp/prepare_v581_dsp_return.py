#!/usr/bin/env python3
"""Complete original DSP boot return with explicit synthetic backend events."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v466_exception_pack import edge
from prepare_v574_dsp_sc import expectations as sc_geometry,install as install_sc,diagnostic
from make_start_to_dsp_return_v64 import EDGES,STOP,END
from apply_aram_binding_v553 import apply as install_aram
PROBE='    static DspStageWitness dsp_stage(v559::expected_stage);'
INCLUDE='#include "wii_boot_sc_binding_v574.h"'
END_SC='        std::cout<<"V574_DSP_SC_RESULT vector=1 rfi=1 blr=1 staged=128 backup=128 flush=4 fallback=0 boot_verified=0"<<std::endl;\n        std::_Exit(0);'
NEXT_SC=END_SC.replace('std::_Exit(0);','''const char* mode=std::getenv("UNDERCOVER_V581_DSP");
        if(!mode||mode[0]!='1'||mode[1]!='\\0'||!dsp_return.begin(cpu,dsp_stage))std::_Exit(114);
        try{dsp_session.emplace(cpu.mmu.mem1,cpu.mmu.mem2,nwii::runtime::hw::pi_intsr,cpu.inst_count);}
        catch(const std::exception&){std::cout<<"V581_DSP_RETURN_INVALID reason=1 stage=1"<<std::endl;std::_Exit(114);}
        std::cout<<"V581_DSP_RETURN_STAGE n=1"<<std::endl;
        return;''')
CONTINUE=PROBE+'''
    static std::optional<DspBootSession> dsp_session;
    static DspReturnWitness dsp_return(v581::expected_return);
    if(dsp_return.stage()){
        const auto before=dsp_return.stage();
        if(!dsp_session||!dsp_return.observe(addr,cpu,dsp_stage,dsp_session->profile())){
            std::cout<<"V581_DSP_RETURN_INVALID reason="<<dsp_return.failure()<<" stage="<<dsp_return.stage()<<std::endl;std::_Exit(114);}
        if(dsp_return.stage()!=before)std::cout<<"V581_DSP_RETURN_STAGE n="<<dsp_return.stage()<<std::endl;
        if(dsp_return.stage()==5u){
            std::cout<<"V581_DSP_RETURN_RESULT reset=2 dma=2 bytes=64 ack=2 mailbox=1 delay=1 restore=128 returned=1 firmware_executed=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
CTX_INCLUDE='#include "undercover/wii_aram_binding_v553.h"'
TICK='  void aram_instruction_boundary() { undercover::wii::AramBinding::advance(inst_count); }'
TICK_NEW='''  void aram_instruction_boundary() {
    try { undercover::wii::DspBootSession::advance(inst_count); }
    catch(const std::exception&) { std::cout<<"V581_DSP_PROFILE_INVALID rejected=1"<<std::endl; std::_Exit(114); }
  }'''
def expectations(data,digest=OWNER_SHA):
    sc_geometry(data,digest)
    rows=[edge(data,site) for site,_ in EDGES]
    if len(rows)!=4 or [r[0] for r in rows]!=[p for _,p in EDGES] or words_at(data,END-4,1)!=(0x4e800020,):
        raise ValueError('DSP return geometry')
    ret=words_at(data,STOP,1)[0]
    if not ret:raise ValueError('DSP return label')
    fmt=lambda r:'VectorEdge{'+','.join(f'0x{v:08x}u' for v in r)+'}'
    header=('#pragma once\n#include "wii_dsp_return_witness_v581.h"\nnamespace undercover::wii::v581 {\n'
        'inline constexpr DspReturnExpectations expected_return{{'+','.join(map(fmt,rows))+'},'+f'0x{ret:08x}u'+'};\n}\n')
    return header,sorted({r[0] for r in rows}),ret
def patch_probe(source):
    source=replace_exact(source,INCLUDE,INCLUDE+'\n#include "v581_private_dsp_return_expectations.h"\n#include "runtime/hw/hw.h"\n#include <optional>')
    return replace_exact(replace_exact(source,PROBE,CONTINUE),END_SC,NEXT_SC)
def patch_context(source):
    source=replace_exact(source,CTX_INCLUDE,CTX_INCLUDE+'\n#include "undercover/wii_dsp_boot_profile_v580.h"\n#include <cstdlib>')
    return replace_exact(source,TICK,TICK_NEW)
def patch_return(source,word):
    pat=re.compile(r'(?mi)^loc_805208D8: ;\n    // 0x805208D8: '+f'{word:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
    if len(pat.findall(source))!=1 or 'V581 audio return' in source:raise ValueError('return label')
    return pat.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x805208D8, ctx); // V581 audio return\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,targets,word=expectations(data,digest)
    counts=dict.fromkeys(targets,0);labels=[]
    for p in generated.glob('output_*.cpp'):
        if p.is_symlink():raise ValueError('symlink')
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        if re.search(r'(?mi)^loc_805208D8: ;$',s):patch_return(s,word);labels.append(p)
    if any(n!=1 for n in counts.values()) or len(labels)!=1:raise ValueError('DSP return trace coverage')
    dest=generated/'nWiiRuntime/include/undercover'
    files={dest/'v581_private_dsp_return_expectations.h':header}
    for name in ('wii_dsp_boot_profile_v580.h','wii_dsp_return_witness_v581.h'):
        files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    install_sc(data,generated,host,digest)
    install_aram(generated,'runtime',host)
    ctx=generated/'nWiiRuntime/include/runtime/cpu_context.h'
    probe=dest/'wii_full_start_probe_v419.h'
    files[ctx]=patch_context(ctx.read_text(encoding='utf-8'))
    files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    shard=labels[0];files[shard]=patch_return(shard.read_text(encoding='utf-8'),word)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as exc:
        print(diagnostic(exc));print('V581_DSP_RETURN_ROUTE installed=0');return 1
    print('V581_DSP_RETURN_ROUTE installed=1 synthetic_backend=1 firmware_executed=0');return 0
if __name__=='__main__':raise SystemExit(main())
