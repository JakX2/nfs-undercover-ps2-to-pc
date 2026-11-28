#!/usr/bin/env python3
"""Original Windows dispatcher-to-native-scheduler entry. No RFI claim.

Only a genuine V920 handler return may admit the original dispatcher BL.
The new gate stops after the native scheduler callee's first generated tick.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import MAX_DOL, replace_exact, direct_bl
from prepare_v667_si_dispatch import DISPATCH
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function, verify_direct
from prepare_v709_os_leaves import owns_root
from prepare_v850_callback_return import LABEL_TICK
from prepare_owner_irq_join_v923 import plan
from prepare_owner_scheduler_v722 import E

def private_header(j, jw, ew):
    return ('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v868 {\n'
            f'inline constexpr uint32_t scheduler_call_pc=0x{j:08x}u,'
            f'scheduler_call_word=0x{jw:08x}u,'
            f'scheduler_entry_pc=0x{E:08x}u,'
            f'scheduler_entry_word=0x{ew:08x}u;\n}}\n')

def patch_binding(s):
    a='#include "v920_private_handler_resume.h"'
    s=replace_exact(s,a,a+'\n#include "v922_private_scheduler_entry.h"')
    a='template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){'
    helpers=r'''inline thread_local bool scheduler_pending=false,scheduler_traced=false;
inline thread_local uint64_t scheduler_tick=0;
inline thread_local uint32_t scheduler_stack=0,scheduler_r2=0,scheduler_r13=0,scheduler_msr=0;
inline bool scheduler_enabled(){
    const char* v=std::getenv("UNDERCOVER_V922_SCHEDULER_ENTRY");
    return v&&v[0]=='1'&&v[1]=='\0';
}
template<class C>void scheduler_start(C& c,uint32_t pc,uint32_t w){
    if(scheduler_pending||scheduler_traced||!dispatch_tick_seen||
       v726::witness.stage()!=5u||pc!=scheduler_call_pc||w!=scheduler_call_word||
       c.pc!=pc||c.lr!=pc||!c.is_running||c.in_callback||c.dispatch_saved_ctx||
       (c.msr&0x8000u)||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
       c.mmu.read32(pc)!=w||!v850::held(c))reject(6);
    scheduler_tick=c.inst_count;scheduler_stack=c.gpr[1];scheduler_r2=c.gpr[2];
    scheduler_r13=c.gpr[13];scheduler_msr=c.msr;scheduler_pending=true;
}
template<class C>bool scheduler_trace(uint32_t addr,C& c){
    if(!scheduler_enabled())return false;
    if(!scheduler_pending||scheduler_traced||addr!=scheduler_entry_pc||
       c.pc!=addr||c.lr!=scheduler_call_pc+4u||c.inst_count!=scheduler_tick||
       c.gpr[1]!=scheduler_stack||c.gpr[2]!=scheduler_r2||
       c.gpr[13]!=scheduler_r13||c.msr!=scheduler_msr||!v850::held(c))reject(6);
    scheduler_traced=true;return true;
}
template<class C>void scheduler_native(C& c,uint32_t pc,uint32_t w){
    if(!scheduler_enabled())return;
    if(!scheduler_pending||!scheduler_traced||pc!=scheduler_entry_pc||
       w!=scheduler_entry_word||c.pc!=pc||c.lr!=scheduler_call_pc+4u||
       c.inst_count!=scheduler_tick+1u||c.gpr[1]!=scheduler_stack||
       c.gpr[2]!=scheduler_r2||c.gpr[13]!=scheduler_r13||
       c.msr!=scheduler_msr||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
       c.mmu.read32(pc)!=w||!v850::held(c))reject(6);
    std::cout<<"V922_SCHEDULER_ENTRY original_handler_return=1 original_dispatcher_branch=1 original_scheduler_entry=1 native_tick=1 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
'''
    s=replace_exact(s,a,helpers+a)
    a='''    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);'''
    return replace_exact(s,a,a.replace('    std::_Exit(0);','    if(scheduler_enabled()){scheduler_start(c,pc,w);return;}\n    std::_Exit(0);'))

def patch_ack(s):
    a='if(v868::active()){v868::observe(a,c);return;}'
    return replace_exact(s,a,'if(v868::scheduler_trace(a,c))return;'+a)

def patch_scheduler(body,pc,word):
    hits=list(LABEL_TICK(pc,word).finditer(body))
    if len(hits)!=1:raise ValueError('scheduler label')
    hook=f'    undercover::wii::v868::scheduler_native(ctx,0x{pc:08x}u,0x{word:08x}u);\n'
    if hook in body:raise ValueError('scheduler duplicate')
    return body[:hits[0].end()]+hook+body[hits[0].end():]

def install(dol,elf,generated):
    roots,j,*_=plan(dol,elf);jw=roots[j][0];ew=roots[E][0]
    if direct_bl(jw,j)!=E:raise ValueError('scheduler call')
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if (len(shards)<20 or not main.is_file() or main.is_symlink() or
        any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards)):
        raise ValueError('scheduler tree')
    src={p:p.read_text(encoding='utf-8') for p in shards};outer=main.read_text(encoding='utf-8')
    audit_native(src.values(),outer,{j:(DISPATCH,jw),E:(E,ew)})
    dispatch=[exact_function(s,DISPATCH) for s in src.values() if owns_root(s,DISPATCH)]
    scheduler=[(p,exact_function(s,E)) for p,s in src.items() if owns_root(s,E)]
    if len(dispatch)!=1 or len(scheduler)!=1:raise ValueError('scheduler owner')
    verify_direct(dispatch[0],j,E)
    path,body=scheduler[0]
    updated=replace_exact(src[path],body,patch_scheduler(body,E,ew))
    inc='#include "undercover/wii_handler_suffix_binding_v868.h"'
    if inc not in updated:
        updated=replace_exact(updated,'#include "runtime/cpu_context.h"',
            '#include "runtime/cpu_context.h"\n'+inc)
    dest=generated/'nWiiRuntime/include/undercover'
    bind=dest/'wii_handler_suffix_binding_v868.h'
    ack=dest/'wii_si_ack_binding_v672.h'
    private=dest/'v922_private_scheduler_entry.h'
    if (dest.is_symlink() or bind.is_symlink() or ack.is_symlink() or
        not bind.is_file() or not ack.is_file() or private.exists() or private.is_symlink()):
        raise ValueError('scheduler destination')
    changes={path:updated,bind:patch_binding(bind.read_text(encoding='utf-8')),
             ack:patch_ack(ack.read_text(encoding='utf-8')),private:private_header(j,jw,ew)}
    for f,data in changes.items():f.write_text(data,encoding='utf-8')
    print('V922_WINDOWS_SCHEDULER_ROUTE installed=1 original_dispatcher=1 native_scheduler_entry=1 guarded=1 default_disabled=1 execution=0 rfi=0 boot_verified=0')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path)
    a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated)
    except (OSError,ValueError,UnicodeError,IndexError,KeyError,struct.error):
        print('V922_WINDOWS_SCHEDULER_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
