#!/usr/bin/env python3
"""Original Windows reschedule return to dispatcher, no-thread-switch path.

Only continue from V924's authentic original reschedule callee. Require
original hint==0, preserved ABI and actual resumed dispatcher label.
A pending thread switch is a real unadmitted dependency, not success.
This does not execute the subsequent context-loader call or RFI.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import MAX_DOL,replace_exact,direct_bl
from prepare_v625_ipc_client import audit_native
from prepare_v667_si_dispatch import DISPATCH
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root
from prepare_owner_irq_join_v923 import plan
from prepare_owner_scheduler_v722 import S
from prepare_v850_callback_return import LABEL_TICK

PREDECESSOR=('V924_WINDOWS_RESCHEDULE_ENTRY original_handler_return=1 scheduler_return=1 '
             'original_reschedule_branch=1 native_entry_tick=1 reschedule_return=0 rfi=0 boot_verified=0')

def private_header(j,branch,word,hint):
    if (direct_bl(branch,j+4)!=S or not -32768<=hint<=32767 or
            not 0<=word<=0xffffffff):
        raise ValueError('reschedule return geometry')
    return ('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v868 {\n'
            f'inline constexpr uint32_t resched_resume_pc=0x{j+8:08x}u,'
            f'resched_resume_word=0x{word:08x}u;\n'
            f'inline constexpr int32_t resched_hint_disp={hint};\n'
            '}\n')

def patch_binding(s):
    a='#include "v924_private_reschedule_entry.h"'
    s=replace_exact(s,a,a+'\n#include "v925_private_reschedule_return.h"')
    a='template<class C>void resched_native(C& c,uint32_t pc,uint32_t w){'
    helpers=r'''inline thread_local bool resched_return_pending=false,resched_return_traced=false;
inline thread_local uint64_t resched_return_tick=0;
inline thread_local uint32_t resched_hint_address=0u;
inline thread_local std::array<uint32_t,32> resched_return_gp{};
inline bool resched_return_enabled(){
    const char* v=std::getenv("UNDERCOVER_V925_RESCHEDULE_RETURN");
    return v&&v[0]=='1'&&v[1]=='\0';
}
[[noreturn]]inline void resched_return_refusal(unsigned code){
    std::cout<<"V925_WINDOWS_RESCHEDULE_RETURN_INVALID reason="<<code<<std::endl;
    std::_Exit(126);
}
template<class C>void resched_return_arm(C& c){
    if(resched_return_pending||resched_return_traced||!resched_pending||
       !resched_traced||c.pc!=reschedule_entry_pc||
       c.lr!=reschedule_branch_pc+4u||c.msr!=resched_msr||
       !c.is_running||c.in_callback||c.dispatch_saved_ctx||
       !v850::held(c))resched_return_refusal(1);
    const int64_t address=int64_t(c.gpr[13])+int64_t(resched_hint_disp);
    if(address<0x80000000ll||address>0x817ffffcll||(address&3ll))resched_return_refusal(2);
    const uint32_t hint=uint32_t(address);
    if(!c.mmu.get_ptr(hint)||!c.mmu.get_ptr(hint+3u))resched_return_refusal(3);
    // A nonzero hint may select an alternate thread. Do not silently skip
    // that original branch or claim the interrupted context was resumed.
    if(c.mmu.read32(hint)!=0u)resched_return_refusal(4);
    resched_hint_address=hint;
    resched_return_gp=c.gpr;
    resched_return_tick=c.inst_count;
    resched_return_pending=true;
}
template<class C>bool resched_return_trace(uint32_t addr,C& c){
    if(!resched_return_enabled())return false;
    if(addr!=resched_resume_pc)return false;
    if(!resched_return_pending||resched_return_traced||c.pc!=addr||
       c.lr!=addr||c.msr!=resched_msr||
       c.gpr[1]!=resched_stack||c.gpr[2]!=resched_r2||
       c.gpr[13]!=resched_r13||
       c.inst_count<=resched_return_tick||
       c.inst_count-resched_return_tick>128u||
       !v850::held(c))resched_return_refusal(5);
    resched_return_traced=true;return true;
}
template<class C>void resched_return_native(C& c,uint32_t pc,uint32_t w){
    if(!resched_return_enabled())return;
    if(!resched_return_pending||!resched_return_traced||
       pc!=resched_resume_pc||w!=resched_resume_word||c.pc!=pc||
       c.lr!=pc||c.msr!=resched_msr||
       !c.is_running||c.in_callback||c.dispatch_saved_ctx||
       c.inst_count<=resched_return_tick+1u||
       c.inst_count-resched_return_tick>128u||
       c.gpr[1]!=resched_stack||c.gpr[2]!=resched_r2||
       c.gpr[13]!=resched_r13||
       !c.mmu.get_ptr(resched_hint_address)||
       c.mmu.read32(resched_hint_address)!=0u||
       !c.mmu.get_ptr(scheduler_counter_address)||
       !c.mmu.get_ptr(scheduler_counter_address+3u)||
       c.mmu.read32(scheduler_counter_address)!=scheduler_initial-1u||
       !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
       c.mmu.read32(pc)!=w||!v850::held(c))resched_return_refusal(6);
    for(unsigned i=14u;i<32u;++i)
        if(c.gpr[i]!=resched_return_gp[i])resched_return_refusal(7);
    std::cout<<"V925_WINDOWS_RESCHEDULE_RETURN scheduler_return=1 original_reschedule_return=1 original_dispatcher_resume=1 no_thread_switch=1 abi=1 context_loader_executed=0 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
'''
    s=replace_exact(s,a,helpers+a)
    a='    std::cout<<"'+PREDECESSOR+'"<<std::endl;\n    std::_Exit(0);'
    return replace_exact(s,a,'    std::cout<<"'+PREDECESSOR+'"<<std::endl;\n'
            '    if(resched_return_enabled()){resched_return_arm(c);return;}\n'
            '    std::_Exit(0);')

# Native dispatcher-resume label is the only admissible return witness.

def patch_resume(body,pc,word):
    hits=list(LABEL_TICK(pc,word).finditer(body))
    if len(hits)!=1:raise ValueError('reschedule resume label')
    trace=f'    (void)undercover::wii::v868::resched_return_trace(0x{pc:08x}u,ctx);\n'
    hook=f'    undercover::wii::v868::resched_return_native(ctx,0x{pc:08x}u,0x{word:08x}u);\n'
    if trace in body or hook in body:raise ValueError('reschedule resume duplicate')
    m=hits[0];tick='    ++ctx.inst_count;\n'
    stamp=body[m.start():m.end()]
    if not stamp.endswith(tick):raise ValueError('reschedule resume tick')
    return body[:m.start()]+stamp[:-len(tick)]+trace+tick+hook+body[m.end():]

def install(dol,elf,generated):
    roots,j,_,_,_,hint,*_=plan(dol,elf)
    branch,word=roots[j][1],roots[j][2]
    private=private_header(j,branch,word,hint)
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if (len(shards)<20 or not main.is_file() or main.is_symlink() or
        any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards)):
        raise ValueError('reschedule return tree')
    src={p:p.read_text(encoding='utf-8') for p in shards};outer=main.read_text(encoding='utf-8')
    audit_native(src.values(),outer,{j+8:(DISPATCH,word)})
    dispatch=[(p,exact_function(s,DISPATCH)) for p,s in src.items() if owns_root(s,DISPATCH)]
    if len(dispatch)!=1:raise ValueError('reschedule return owner')
    verify_direct(dispatch[0][1],j+4,S)
    p,body=dispatch[0]
    updated=replace_exact(src[p],body,patch_resume(body,j+8,word))
    dest=generated/'nWiiRuntime/include/undercover'
    bind=dest/'wii_handler_suffix_binding_v868.h'
    header=dest/'v925_private_reschedule_return.h'
    if (dest.is_symlink() or bind.is_symlink() or
        not bind.is_file() or header.exists() or header.is_symlink()):
        raise ValueError('reschedule return destination')
    changes={p:updated,bind:patch_binding(bind.read_text(encoding='utf-8')),
             header:private}
    for path,contents in changes.items():path.write_text(contents,encoding='utf-8')
    print('V925_WINDOWS_RESCHEDULE_RETURN_ROUTE installed=1 original_no_switch=1 dispatcher_resume=1 default_disabled=1 execution=0 rfi=0 boot_verified=0')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dol',type=Path);parser.add_argument('elf',type=Path)
    parser.add_argument('generated',type=Path);a=parser.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:
            raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated)
    except (OSError,ValueError,UnicodeError,IndexError,KeyError,struct.error):
        print('V925_WINDOWS_RESCHEDULE_RETURN_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
