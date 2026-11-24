#!/usr/bin/env python3
"""Compose private first IOS_Open through synchronous submission entry."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,OWNER_SHA,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256
from make_v639_open_geometry import geometry,render,exact_words,STOP
from prepare_v629_stm_open import install as install_stm,INCLUDE as PRIOR_INCLUDE
from prepare_v625_ipc_client import audit_native,patch_return
INCLUDE='#include "v629_private_stm_expectations.h"'
DECL='    static StmPrefixWitness stm_prefix(v629::expected_stm);'
RESULT='            std::cout<<"V629_STM_RESULT entry=1 open=1 pathname="<<stm_prefix.path_kind()<<" mode=0 native_transport=1 serviced=0 actual_ios=0 fallback=0 boot_verified=0"<<std::endl;\n            std::_Exit(0);'
NEXT=DECL+'''
    static OpenRequestWitness open_request(v639::expected_open);
    if(open_request.stage()){
        if(v641::vector_trace(addr,cpu))return;
        if(!open_request.observe(addr,cpu,v641::route)){
            std::cout<<"V641_OPEN_INVALID reason="<<open_request.failure()<<" stage="<<open_request.stage()<<std::endl;std::_Exit(122);}
        std::cout<<"V641_OPEN_STAGE n="<<open_request.stage()<<std::endl;
        if(open_request.stage()==9u){
            std::cout<<"V641_OPEN_RESULT allocation=1 irq_restore=1 flush=1 vector=1 request=1 submitted=0 serviced=0 fallback=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }'''
CONT=RESULT.replace('std::_Exit(0);','''const char* next=std::getenv("UNDERCOVER_V641_OPEN");
            if(!next||next[0]!='1'||next[1]!='\\0'||!open_request.begin(cpu,stm_prefix.path_kind(),ipc_client.heap_size())){
                std::cout<<"V641_OPEN_INVALID reason=1 stage=0"<<std::endl;std::_Exit(122);}
            v641::active=true;
            std::cout<<"V641_OPEN_STAGE n=1"<<std::endl;''')
IOS_INC='#include "undercover/wii_arena_binding_v609.h"'
IOS_HOOK='  if (undercover::wii::v609::try_sc(ctx)) return false;'
OLD_SC='    if (nwii::runtime::g_trace_calls) nwii::runtime::trace_call(0x805222E8, ctx); // V559 pre-SC staging checkpoint\n'
NEW_SC='    if (nwii::runtime::g_trace_calls) { ctx.pc = 0x805222E8; nwii::runtime::trace_call(0x805222E8, ctx); } // V641 exact pre-SC PC\n'
def patch_probe(s):
    return replace_exact(replace_exact(replace_exact(s,INCLUDE,INCLUDE+'\n#include "v639_private_open_expectations.h"\n#include "wii_open_binding_v641.h"'),DECL,NEXT),RESULT,CONT)
def patch_ios(s):
    return replace_exact(replace_exact(s,IOS_INC,IOS_INC+'\n#include "undercover/wii_open_binding_v641.h"'),IOS_HOOK,'  if (undercover::wii::v641::try_sc(ctx)) return false;\n'+IOS_HOOK)
def patch_sc(s):
    anchor='loc_805222E8: ;\n    // 0x805222E8: 44000002\n'+OLD_SC+'    ++ctx.inst_count;\n'
    if s.count(anchor)!=1 or s.count(OLD_SC)!=1:raise ValueError('open SC label')
    return s.replace(OLD_SC,NEW_SC,1)
def install(dol,elf,generated,host,dd=OWNER_SHA,ed=ORIGINAL_SHA256):
    g=geometry(dol,elf,dd,ed);rows,extra,blocks=g
    expected={pc+4*i:(pc,w) for pc,words in blocks.items() for i,w in enumerate(words)}
    for target,_,_,word in rows:
        if target not in blocks:expected[target]=(target,word)
    paths=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('open tree')
    n=audit_native((p.read_text(encoding='utf-8') for p in paths),main.read_text(encoding='utf-8'),expected)
    targets={r[0] for r in rows}|{0x8051ab34};counts=dict.fromkeys(targets,0)
    resume=0x80519a1c;owners={}
    for p in paths:
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
        for pc in (resume,0x805222e8):
            if re.search(r'(?mi)^loc_'+f'{pc:X}'+r': ;$',s):
                if pc in owners:raise ValueError('open duplicate label')
                owners[pc]=p
    if any(v!=1 for v in counts.values()) or set(owners)!={resume,0x805222e8}:raise ValueError('open trace coverage')
    rt=generated/'nWiiRuntime';dest=rt/'include/undercover'
    files={dest/'v639_private_open_expectations.h':render(g)}
    for name in ('wii_open_request_witness_v639.h','wii_open_sc_route_v637.h','wii_open_binding_v641.h'):
        files[dest/name]=(host/name).read_text(encoding='utf-8')
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files):raise ValueError('open destination')
    install_stm(dol,elf,generated,host,dd,ed)
    probe=dest/'wii_full_start_probe_v419.h';ios=rt/'src/hle/ios.cpp'
    files[probe]=patch_probe(probe.read_text(encoding='utf-8'))
    files[ios]=patch_ios(ios.read_text(encoding='utf-8'))
    p=owners[resume];files[p]=patch_return(p.read_text(encoding='utf-8'),extra[2],resume)
    p=owners[0x805222e8];files[p]=patch_sc(files[p] if p in files else p.read_text(encoding='utf-8'))
    for p,s in files.items():p.write_text(s,encoding='utf-8')
    return n
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('identity')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        allow={'open tree','open duplicate label','open trace coverage','open destination','open SC label','source seam','identity','open extent','allocator tail','return geometry','open edge','word identity','native IPC label identity','native IPC label body','native IPC duplicate root','native IPC coverage','native IPC dispatch','native IPC return label'}
        why=str(e) if str(e) in allow else 'prior_or_io'
        print('V641_OPEN_ROUTE installed=0 reason='+why.replace(' ','_'));return 1
    print(f'V641_OPEN_ROUTE installed=1 native_words={n} edges=6 tail=1 request_boundary=1 actual_ios=0');return 0
if __name__=='__main__':raise SystemExit(main())
