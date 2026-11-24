#!/usr/bin/env python3
"""Compose authenticated original DSP stage and bounded native SC return."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,replace_exact
from prepare_v559_dsp_stage import expectations as stage_geometry,install as install_stage
from apply_sc_dispatch_gate_v572 import install as gate
from make_start_to_dsp_stage_v63 import STOP
SOURCE=0x805290a8
RETURN=STOP
HEADER='#include "runtime/cpu_context.h"'
HOOK='bool handle_syscall(CPUContext &ctx) {'
HOOK_NEW=HOOK+'\n  if (undercover::wii::v574::try_sc(ctx)) return false;'
INCLUDE='#include "v559_private_dsp_stage_expectations.h"'
PROBE='    static DspStageWitness dsp_stage(v559::expected_stage);'
END='        if(dsp_stage.stage()==6u){std::cout<<"V559_DSP_STAGE_RESULT backup=1 image=128 flush=4 sc_entry=1 sc_executed=0 fallback=0 boot_verified=0"<<std::endl;std::_Exit(0);}'
NEXT=END.replace('std::_Exit(0);','v574::arm(addr,cpu);')
PRE=PROBE+'''
    if(v574::vector_trace(addr,cpu))return;
    if(dsp_stage.stage()==6u){
        if(!v574::route.returned(cpu)||!dsp_stage.finish_sc(addr,cpu,v574::return_word))v574::reject();
        std::cout<<"V574_DSP_SC_STAGE n=4"<<std::endl;
        std::cout<<"V574_DSP_SC_RESULT vector=1 rfi=1 blr=1 staged=128 backup=128 flush=4 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }'''
def expectations(data,digest=OWNER_SHA):
    stage_geometry(data,digest)
    vector=words_at(data,SOURCE,7)
    if vector[-1]!=0x4c000064 or any(w>>26 in (16,17,18) or (w>>26==19 and w!=0x4c00012c) for w in vector[:-1]):
        raise ValueError('SC vector geometry')
    ret=words_at(data,RETURN,1)[0]
    if not ret:raise ValueError('DSP return geometry')
    raw=struct.pack('>7I',*vector)
    header=('#pragma once\n#include <array>\n#include <cstdint>\nnamespace undercover::wii::v574 {\n'
        'inline constexpr std::array<uint8_t,28> expected_vector{'+','.join(map(str,raw))+'};\n'
        f'inline constexpr uint32_t return_word=0x{ret:08x}u;\n'+'}\n')
    return header,vector,ret
def patch_probe(source):
    source=replace_exact(source,INCLUDE,INCLUDE+'\n#include "wii_boot_sc_binding_v574.h"')
    return replace_exact(replace_exact(source,PROBE,PRE),END,NEXT)
def patch_ios(source):
    return replace_exact(replace_exact(source,HEADER,HEADER+'\n#include "undercover/wii_boot_sc_binding_v574.h"'),HOOK,HOOK_NEW)
def patch_return(source,word):
    pattern=re.compile(r'(?mi)^loc_80522044: ;\n    // 0x80522044: '+f'{word:08X}'+r'\n(?=    \+\+ctx\.inst_count;)')
    if len(pattern.findall(source))!=1 or 'V574 original DSP flush return' in source:raise ValueError('return trace')
    return pattern.sub(lambda m:m[0]+'    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x80522044, ctx); // V574 original DSP flush return\n',source,count=1)
def install(data,generated,host,digest=OWNER_SHA):
    header,vector,ret=expectations(data,digest)
    rt=generated/'nWiiRuntime';dest=rt/'include/undercover';ios=rt/'src/hle/ios.cpp'
    if dest.is_symlink() or ios.is_symlink():raise ValueError('destination')
    files={dest/'v574_private_sc_expectations.h':header}
    for name in ('native_sc_vector_v63.h','wii_boot_sc_route_v570.h','wii_boot_sc_binding_v574.h'):
        files[dest/name]=(host/name).read_text(encoding='utf-8')
    if any(p.exists() or p.is_symlink() for p in files):raise ValueError('destination')
    new_ios=patch_ios(ios.read_text(encoding='utf-8'))
    labels=[]
    for p in generated.glob('output_*.cpp'):
        if p.is_symlink():raise ValueError('source symlink')
        s=p.read_text(encoding='utf-8')
        if re.search(r'(?mi)^loc_80522044: ;$',s):patch_return(s,ret);labels.append(p)
    if len(labels)!=1:raise ValueError('return coverage')
    gate(generated,vector)
    install_stage(data,generated,host,digest)
    probe=dest/'wii_full_start_probe_v419.h';files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    files[ios]=new_ios
    shard=labels[0];files[shard]=patch_return(shard.read_text(encoding='utf-8'),ret)
    for p,s in files.items():p.write_text(s,encoding='utf-8')
def diagnostic(exc):
    # Only source provenance from tracked, original-free preparation code.
    # Never publish exception strings, traceback source, private paths,
    # generated C++, register values, owner bytes or unbounded fields.
    import traceback
    host=Path(__file__).resolve().parent
    frames=traceback.extract_tb(exc.__traceback__)
    allowed={'ValueError','OSError','UnicodeError','error','FileNotFoundError','PermissionError','UnicodeDecodeError'}
    kind=type(exc).__name__
    if kind not in allowed:kind='Other'
    known={
        'source seam':'source_seam','destination':'destination','destination exists':'destination',
        'predecessor':'predecessor','header conflict':'header_conflict',
        'return trace':'return_trace','return coverage':'return_coverage',
        'SC vector geometry':'sc_geometry','DSP return geometry':'dsp_return',
        'DSP staging geometry':'dsp_geometry','DSP trace coverage':'dsp_trace',
        'thread trace coverage':'thread_trace','audio trace coverage':'audio_trace',
        'SRAM trace coverage':'sram_trace','trace coverage':'trace_coverage',
        'SC label':'sc_label','return label':'return_label',
        'vector definition':'vector_definition','vector instruction provenance':'vector_provenance',
        'vector native instruction coverage':'vector_native','vector fallback':'vector_fallback',
        'dispatcher geometry':'dispatcher_geometry','vector RFI':'vector_rfi',
        'native declaration':'native_declaration','generated tree':'generated_tree',
        'source symlink':'symlink','symlink':'symlink','owner identity':'owner_identity',
        'text mapping':'text_mapping','text geometry':'text_geometry',
        'missing original function symbol table or startup':'symbol_map',
    }
    reason=known.get(str(exc),'other')
    for f in reversed(frames):
        path=Path(f.filename)
        if (path.parent.resolve()==host and path.is_file() and
            re.fullmatch(r'(?:prepare|apply|make)_v?[A-Za-z0-9_]{1,100}\.py',path.name) and
            1<=f.lineno<=10000):
            return f'V577_DSP_SC_PREP_FAILURE file={path.name} line={f.lineno} kind={kind} reason={reason}'
    return f'V577_DSP_SC_PREP_FAILURE file=unknown line=0 kind={kind} reason={reason}'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dol',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL:raise ValueError('size')
        install(a.dol.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as exc:
        print(diagnostic(exc));print('V574_DSP_SC_ROUTE installed=0');return 1
    print('V574_DSP_SC_ROUTE installed=1 direct_only=1 ios_delegation=1');return 0
if __name__=='__main__':raise SystemExit(main())
