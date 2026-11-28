#!/usr/bin/env python3
"""Original Windows scheduler-enable ABI return, before reschedule call.

Requires the V922 native scheduler-entry witness, authentic original
scheduler, disable/restore callees, and a real dispatcher return. This is
a private original-image observer, not emulation or a context-switch stub.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import struct
from prepare_v419_full_start import MAX_DOL, replace_exact, direct_bl
from prepare_v625_ipc_client import audit_native
from prepare_v667_si_dispatch import DISPATCH
from prepare_v680_si_helper import exact_function, verify_direct
from prepare_v709_os_leaves import owns_root
from prepare_owner_irq_join_v923 import plan
from prepare_owner_scheduler_v722 import E, S, reachable
from prepare_v850_callback_return import LABEL_TICK

MARKER=('V922_SCHEDULER_ENTRY original_handler_return=1 original_dispatcher_branch=1 '
        'original_scheduler_entry=1 native_tick=1 rfi=0 boot_verified=0')


def private_header(j, return_word, disable, restore, calls, counter):
    if (len(calls)!=2 or [target for _, target in calls]!=[disable,restore] or
            not -32768<=counter<=32767 or direct_bl(return_word,j+4)!=S):
        raise ValueError('scheduler private shape')
    return ('#pragma once\n#include <array>\n#include <cstdint>\n'
            'namespace undercover::wii::v868 {\n'
            f'inline constexpr uint32_t scheduler_return_pc=0x{j+4:08x}u,'
            f'scheduler_return_word=0x{return_word:08x}u,'
            f'scheduler_disable_pc=0x{disable:08x}u,'
            f'scheduler_restore_pc=0x{restore:08x}u,'
            f'scheduler_disable_lr=0x{calls[0][0]+4:08x}u,'
            f'scheduler_restore_lr=0x{calls[1][0]+4:08x}u;\n'
            f'inline constexpr int32_t scheduler_counter_disp={counter};\n'
            '}\n')


def patch_binding(s):
    a='#include "v922_private_scheduler_entry.h"'
    s=replace_exact(s,a,a+'\n#include "v923_private_scheduler_return.h"')
    a='template<class C>void scheduler_native(C& c,uint32_t pc,uint32_t w){'
    helpers=r'''inline thread_local std::array<uint32_t,32> scheduler_return_gp{};
inline thread_local unsigned scheduler_dependency_stage=0u;
inline thread_local uint32_t scheduler_counter_address=0u,scheduler_initial=0u;
inline bool scheduler_return_enabled(){
    const char* v=std::getenv("UNDERCOVER_V923_SCHEDULER_RETURN");
    return v&&v[0]=='1'&&v[1]=='\0';
}
template<class C>void scheduler_return_arm(C& c){
    if(!scheduler_enabled()||!scheduler_pending||!scheduler_traced||
       scheduler_dependency_stage||c.msr!=scheduler_msr||!v850::held(c))reject(6);
    const int64_t address=int64_t(c.gpr[13])+int64_t(scheduler_counter_disp);
    if(address<0x80000000ll||address>0x817ffffcll||(address&3ll))reject(6);
    const uint32_t addr=uint32_t(address);
    if(!c.mmu.get_ptr(addr)||!c.mmu.get_ptr(addr+3u))reject(6);
    scheduler_counter_address=addr;scheduler_initial=c.mmu.read32(addr);
    if(scheduler_initial==0u||scheduler_initial>1024u)reject(6);
    scheduler_return_gp=c.gpr;
    scheduler_dependency_stage=1u;
}
template<class C>bool scheduler_return_trace(uint32_t addr,C& c){
    if(!scheduler_return_enabled())return false;
    if(addr!=scheduler_disable_pc&&addr!=scheduler_restore_pc)return false;
    const bool disable=addr==scheduler_disable_pc;
    if(!scheduler_pending||!scheduler_traced||
       scheduler_dependency_stage!=(disable?1u:2u)||
       c.pc!=addr||c.lr!=(disable?scheduler_disable_lr:scheduler_restore_lr)||
       c.msr!=scheduler_msr||c.gpr[1]!=scheduler_stack||
       c.gpr[2]!=scheduler_r2||c.gpr[13]!=scheduler_r13||
       c.inst_count<=scheduler_tick||c.inst_count-scheduler_tick>512u||
       !v850::held(c))reject(6);
    ++scheduler_dependency_stage;return true;
}
template<class C>void scheduler_return(C& c,uint32_t pc,uint32_t w){
    if(!scheduler_return_enabled())return;
    if(!scheduler_pending||!scheduler_traced||scheduler_dependency_stage!=3u||
       pc!=scheduler_return_pc||w!=scheduler_return_word||c.pc!=pc||
       c.lr!=pc||c.msr!=scheduler_msr||c.inst_count<=scheduler_tick||
       c.inst_count-scheduler_tick>512u||
       c.gpr[1]!=scheduler_stack||c.gpr[2]!=scheduler_r2||
       c.gpr[13]!=scheduler_r13||c.gpr[3]!=scheduler_initial||
       !c.mmu.get_ptr(scheduler_counter_address)||
       c.mmu.read32(scheduler_counter_address)!=scheduler_initial-1u||
       !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
       c.mmu.read32(pc)!=w||!v850::held(c))reject(6);
    for(unsigned i=14u;i<32u;++i)
        if(c.gpr[i]!=scheduler_return_gp[i])reject(6);
    std::cout<<"V923_WINDOWS_SCHEDULER_RETURN original_handler_return=1 original_enable=1 disable=1 restore=1 counter=1 abi=1 reschedule_executed=0 rfi=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
'''
    s=replace_exact(s,a,helpers+a)
    a='    std::cout<<"'+MARKER+'"<<std::endl;\n    std::_Exit(0);'
    return replace_exact(s,a,
        '    std::cout<<"'+MARKER+'"<<std::endl;\n'
        '    if(scheduler_return_enabled()){scheduler_return_arm(c);return;}\n'
        '    std::_Exit(0);')


# Observe disable and restore through their real translated callee labels.

def patch_dependency(body,pc,word):
    hits=list(LABEL_TICK(pc,word).finditer(body))
    if len(hits)!=1:raise ValueError('scheduler dependency label')
    hook=f'    (void)undercover::wii::v868::scheduler_return_trace(0x{pc:08x}u,ctx);\n'
    if hook in body:raise ValueError('scheduler dependency duplicate')
    m=hits[0];tick='    ++ctx.inst_count;\n'
    stamp=body[m.start():m.end()]
    if not stamp.endswith(tick):raise ValueError('scheduler dependency tick')
    return body[:m.start()]+stamp[:-len(tick)]+hook+tick+body[m.end():]


def patch_dispatcher(body,pc,word):
    hits=list(LABEL_TICK(pc,word).finditer(body))
    if len(hits)!=1:raise ValueError('scheduler return label')
    hook=f'    undercover::wii::v868::scheduler_return(ctx,0x{pc:08x}u,0x{word:08x}u);\n'
    if hook in body:raise ValueError('scheduler return duplicate')
    return body[:hits[0].end()]+hook+body[hits[0].end():]


def install(dol,elf,generated):
    roots,j,_,_,counter,_,disable,restore,_,calls,*_=plan(dol,elf)
    word=roots[j][1];head=private_header(j,word,disable,restore,calls,counter)
    shards=sorted(generated.glob('output_*.cpp'));main=generated/'main_output.cpp'
    if (len(shards)<20 or not main.is_file() or main.is_symlink() or
        any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards)):
        raise ValueError('scheduler return tree')
    src={p:p.read_text(encoding='utf-8') for p in shards};outer=main.read_text(encoding='utf-8')
    expected={j+4:(DISPATCH,word)}
    for owner in (E,disable,restore):
        ws=roots[owner]
        expected.update({pc:(owner,ws[(pc-owner)//4]) for pc in reachable(owner,ws)})
    audit_native(src.values(),outer,expected)
    dispatch=[(p,exact_function(s,DISPATCH)) for p,s in src.items() if owns_root(s,DISPATCH)]
    enable=[exact_function(s,E) for s in src.values() if owns_root(s,E)]
    if len(dispatch)!=1 or len(enable)!=1:raise ValueError('scheduler return owner')
    verify_direct(dispatch[0][1],j+4,S)
    for site,target in calls:verify_direct(enable[0],site,target)
    p,body=dispatch[0]
    changes={p:replace_exact(src[p],body,patch_dispatcher(body,j+4,word))}
    include='#include "undercover/wii_handler_suffix_binding_v868.h"'
    for target in (disable,restore):
        owners=[(p,exact_function(s,target)) for p,s in src.items() if owns_root(s,target)]
        if len(owners)!=1:raise ValueError('scheduler dependency owner')
        path,owned=owners[0]
        old=changes.get(path,src[path])
        new=replace_exact(old,owned,patch_dependency(owned,target,roots[target][0]))
        if include not in new:
            new=replace_exact(new,'#include "runtime/cpu_context.h"',
                '#include "runtime/cpu_context.h"\n'+include)
        changes[path]=new
    dest=generated/'nWiiRuntime/include/undercover'
    bind=dest/'wii_handler_suffix_binding_v868.h'
    private=dest/'v923_private_scheduler_return.h'
    if (dest.is_symlink() or bind.is_symlink() or
        not bind.is_file() or private.exists() or private.is_symlink()):
        raise ValueError('scheduler return destination')
    changes.update({bind:patch_binding(bind.read_text(encoding='utf-8')),private:head})
    for path,contents in changes.items():path.write_text(contents,encoding='utf-8')
    print('V923_WINDOWS_SCHEDULER_RETURN_ROUTE installed=1 original_enable=1 two_original_leaves=1 dispatcher_resume=1 guarded=1 default_disabled=1 execution=0 rfi=0 boot_verified=0')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('dol',type=Path);parser.add_argument('elf',type=Path)
    parser.add_argument('generated',type=Path)
    a=parser.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:
            raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated)
    except (OSError,ValueError,UnicodeError,IndexError,KeyError,struct.error):
        print('V923_WINDOWS_SCHEDULER_RETURN_ROUTE installed=0');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
