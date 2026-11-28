#!/usr/bin/env python3
"""Real original dispatcher -> reschedule function native Windows entry.

Require completed V923 enable/disable/restore and its authentic dispatcher
resumption. Observe a real generated original reschedule instruction tick.
No reschedule return, thread switch, RFI or game-main claims.
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

PREDECESSOR=('V923_WINDOWS_SCHEDULER_RETURN original_handler_return=1 original_enable=1 '
             'disable=1 restore=1 counter=1 abi=1 reschedule_executed=0 rfi=0 boot_verified=0')

def private_header(j,branch,entry):
    if direct_bl(branch,j+4)!=S or not 0<=entry<=0xffffffff:
        raise ValueError('reschedule geometry')
    return ('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v868 {\n'
            f'inline constexpr uint32_t reschedule_branch_pc=0x{j+4:08x}u,'
            f'reschedule_branch_word=0x{branch:08x}u,'
            f'reschedule_entry_pc=0x{S:08x}u,'
            f'reschedule_entry_word=0x{entry:08x}u;\n'
            '}\n')

def patch_binding(s):
    a='#include "v923_private_scheduler_return.h"'
    s=replace_exact(s,a,a+'\n#include "v924_private_reschedule_entry.h"')
    a='template<class C>void scheduler_return(C& c,uint32_t pc,uint32_t w){'
    helpers=r'''inline thread_local bool resched_pending=false,resched_traced=false;
inline thread_local uint64_t resched_tick=0;
inline thread_local uint32_t resched_stack=0,resched_r2=0,resched_r13=0;
inline thread_local uint32_t resched_msr=0,resched_arg=0;
inline bool resched_enabled(){
    const char* v=std::getenv("UNDERCOVER_V924_RESCHEDULE_ENTRY");
    return v&&v[0]=='1'&&v[1]=='\0';
}
[[noreturn]]inline void resched_refusal(unsigned code){
    std::cout<<"V924_WINDOWS_RESCHEDULE_ENTRY_INVALID reason="<<code<<std::endl;
    std::_Exit(126);
}
template<class C>void resched_arm(C& c,uint32_t pc,uint32_t w){
    if(resched_pending||resched_traced||!scheduler_return_enabled()||
       scheduler_dependency_stage!=3u||pc!=reschedule_branch_pc||
       w!=reschedule_branch_word||c.pc!=pc||c.lr!=pc||
       c.msr!=scheduler_msr||!v850::held(c))resched_refusal(1);
    resched_tick=c.inst_count;resched_stack=c.gpr[1];resched_r2=c.gpr[2];
    resched_r13=c.gpr[13];resched_msr=c.msr;resched_arg=c.gpr[3];
    resched_pending=true;
}
template<class C>bool resched_trace(uint32_t addr,C& c){
    // A separate original rescheduler call is not a V924 witness.
    if(!resched_enabled()||!resched_pending)return false;
    if(addr!=reschedule_entry_pc)return false;
    if(!resched_pending||resched_traced||c.pc!=addr||
       c.lr!=reschedule_branch_pc+4u||c.inst_count!=resched_tick||
       c.gpr[1]!=resched_stack||c.gpr[2]!=resched_r2||
       c.gpr[13]!=resched_r13||c.gpr[3]!=resched_arg||
       c.msr!=resched_msr||!v850::held(c))resched_refusal(2);
    resched_traced=true;return true;
}
template<class C>void resched_native(C& c,uint32_t pc,uint32_t w){
    if(!resched_enabled()||!resched_pending)return;
    if(!resched_pending||!resched_traced||pc!=reschedule_entry_pc||
       w!=reschedule_entry_word||c.pc!=pc||
       c.lr!=reschedule_branch_pc+4u||c.inst_count!=resched_tick+1u||
       c.gpr[1]!=resched_stack||c.gpr[2]!=resched_r2||
       c.gpr[13]!=resched_r13||c.gpr[3]!=resched_arg||
       c.msr!=resched_msr||!c.mmu.get_ptr(pc)||
       !c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w||
       !scheduler_held_after_tick(c))resched_refusal(3);
    std::cout<<"V924_WINDOWS_RESCHEDULE_ENTRY original_handler_return=1 scheduler_return=1 original_reschedule_branch=1 native_entry_tick=1 reschedule_return=0 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
'''
    s=replace_exact(s,a,helpers+a)
    a='    std::cout<<"'+PREDECESSOR+'"<<std::endl;\n    std::_Exit(0);'
    return replace_exact(s,a,'    std::cout<<"'+PREDECESSOR+'"<<std::endl;\n'
            '    if(resched_enabled()){resched_arm(c,pc,w);return;}\n'
            '    std::_Exit(0);')

# A translated branch target, not a memory/interrupt observer, proves entry.

def patch_native(body,pc,word):
    hits=list(LABEL_TICK(pc,word).finditer(body))
    if len(hits)!=1:raise ValueError('reschedule label')
    trace=f'    (void)undercover::wii::v868::resched_trace(0x{pc:08x}u,ctx);\n'
    hook=f'    undercover::wii::v868::resched_native(ctx,0x{pc:08x}u,0x{word:08x}u);\n'
    if trace in body or hook in body:raise ValueError('reschedule duplicate')
    m=hits[0];tick='    ++ctx.inst_count;\n'
    stamp=body[m.start():m.end()]
    if not stamp.endswith(tick):raise ValueError('reschedule tick')
    return body[:m.start()]+stamp[:-len(tick)]+trace+tick+hook+body[m.end():]

def install(dol,elf,generated):
    roots,j,*_=plan(dol,elf)
    branch,entry=roots[j][1],roots[S][0]
    private=private_header(j,branch,entry)
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if (len(shards)<20 or not main.is_file() or main.is_symlink() or
        any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards)):
        raise ValueError('reschedule tree')
    src={p:p.read_text(encoding='utf-8') for p in shards};outer=main.read_text(encoding='utf-8')
    audit_native(src.values(),outer,{j+4:(DISPATCH,branch),S:(S,entry)})
    dispatch=[exact_function(s,DISPATCH) for s in src.values() if owns_root(s,DISPATCH)]
    callee=[(p,exact_function(s,S)) for p,s in src.items() if owns_root(s,S)]
    if len(dispatch)!=1 or len(callee)!=1:raise ValueError('reschedule owner')
    verify_direct(dispatch[0],j+4,S)
    p,body=callee[0]
    updated=replace_exact(src[p],body,patch_native(body,S,entry))
    include='#include "undercover/wii_handler_suffix_binding_v868.h"'
    if include not in updated:
        updated=replace_exact(updated,'#include "runtime/cpu_context.h"',
            '#include "runtime/cpu_context.h"\n'+include)
    dest=generated/'nWiiRuntime/include/undercover'
    bind=dest/'wii_handler_suffix_binding_v868.h'
    header=dest/'v924_private_reschedule_entry.h'
    if (dest.is_symlink() or bind.is_symlink() or
        not bind.is_file() or header.exists() or header.is_symlink()):
        raise ValueError('reschedule destination')
    changes={p:updated,bind:patch_binding(bind.read_text(encoding='utf-8')),
             header:private}
    for path,contents in changes.items():path.write_text(contents,encoding='utf-8')
    print('V924_WINDOWS_RESCHEDULE_ROUTE installed=1 original_dispatcher_branch=1 original_reschedule_entry=1 guarded=1 default_disabled=1 execution=0 rfi=0 boot_verified=0')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dol',type=Path);parser.add_argument('elf',type=Path)
    parser.add_argument('generated',type=Path);a=parser.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:
            raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated)
    except (OSError,ValueError,UnicodeError,IndexError,KeyError,struct.error):
        print('V924_WINDOWS_RESCHEDULE_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
