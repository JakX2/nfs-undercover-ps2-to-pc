#!/usr/bin/env python3
"""Opt-in continuation of V919 through real native handler BLR and dispatcher resume."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import geometry,DISPATCH,exact
from prepare_owner_handler_tail_v879 import plan
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v884_handler_tail import patch_label as previous_patch

def patch_label(body,pc,w):
    # Reuse the checked V884 pre/post tick seam, not its separate witness.
    out=previous_patch(body,pc,w,'resume')
    return out.replace('v884::dispatch_resume','v868::dispatch_resume').replace(
        'v884::resume','v868::dispatcher_resume').replace('v884::active()','v868::return_active()')

def patch_binding(s):
    a='#include "v919_private_handler_epilogue.h"'
    s=replace_exact(s,a,a+'\n#include "v920_private_handler_resume.h"')
    a='inline thread_local HandlerSuffixGuard epilogue_guard;'
    s=replace_exact(s,a,a+'''
inline thread_local bool dispatch_tick_seen=false;
inline bool return_enabled(){const char* v=std::getenv("UNDERCOVER_V920_HANDLER_RETURN");return v&&v[0]=='1'&&v[1]=='\\0';}
inline bool return_active(){return return_enabled()&&active()&&v726::witness.stage()>=3u;}
''')
    a='            std::_Exit(0);\n        }\n        if(v726::witness.stage()!=2u)reject(6);'
    s=replace_exact(s,a,'''            if(!return_enabled())std::_Exit(0);
            return true;
        }
        if(v726::witness.stage()!=2u)reject(6);''')
    a='template<class C>bool poll(C& c){'
    s=replace_exact(s,a,'''template<class C>void dispatch_resume(C& c,uint32_t pc,uint32_t w){
    if(!return_active())return;
    if(dispatch_tick_seen||v726::witness.stage()!=4u||pc!=dispatcher_resume_pc||
       w!=dispatcher_resume_word||c.pc!=pc||c.lr!=pc||
       !observe_completed_callback_dispatch(si_transfer_device,c.inst_count)||
       (v861::active()&&!v861::device.observe_dispatch(c.inst_count))||!v850::held(c))reject(6);
    dispatch_tick_seen=true;
}
template<class C>void dispatcher_resume(C& c,uint32_t pc,uint32_t w){
    if(!return_active())return;
    if(!dispatch_tick_seen||!advance_restore(c)||!v726::witness.resumed(c,pc,w,true)||
       v726::witness.stage()!=5u)reject(6);
    std::cout<<"V920_HANDLER_RETURN original_blr=1 original_dispatcher=1 abi=1 outer_tick=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
'''+a)
    a='    if(!v850::held(c)||!v726::witness.poll(c,true))reject(5);'
    return replace_exact(s,a,a+'''
    if(return_active()){
        if(v726::witness.stage()!=4u||dispatch_tick_seen||c.pc!=dispatcher_resume_pc)reject(5);
        std::cout<<"V920_HANDLER_POLL original_blr=1 same_tick=1"<<std::endl;
    }''')

def install(dol,elf,root):
    # The original four-word epilogue and original fifteen-GPR restore
    # were authenticated independently in V879. Require that same shape.
    plan(dol,elf)
    _,(site,_),_,_,_=geometry(dol,elf)
    resume=site+4;word=exact(dol,elf,resume,1)[0]
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('return tree')
    outer=main.read_text();verify_resume_dispatch(outer,DISPATCH,resume)
    owners=[]
    for p in paths:
        s=p.read_text()
        if owns_root(s,DISPATCH):owners.append((p,s))
    if len(owners)!=1:raise ValueError('return owner')
    p,s=owners[0];body=exact_function(s,DISPATCH)
    if audit_native([body],outer,{resume:(DISPATCH,word)})!=1:raise ValueError('return coverage')
    s=replace_exact(s,body,patch_label(body,resume,word))
    inc='#include "undercover/wii_handler_suffix_binding_v868.h"'
    if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
    dest=root/'nWiiRuntime/include/undercover';binding=dest/'wii_handler_suffix_binding_v868.h';header=dest/'v920_private_handler_resume.h'
    if dest.is_symlink() or binding.is_symlink() or not binding.is_file() or header.exists() or header.is_symlink():
        raise ValueError('return destination')
    patched=patch_binding(binding.read_text())
    h='#pragma once\n#include <cstdint>\nnamespace undercover::wii::v868 {\n'
    h+=f'inline constexpr uint32_t dispatcher_resume_pc=0x{resume:08x}u,dispatcher_resume_word=0x{word:08x}u;\n}}\n'
    for f,data in ((p,s),(binding,patched),(header,h)):f.write_text(data)
    print('V920_HANDLER_RETURN_ROUTE installed=1 original_epilogue=4 dispatcher_resume=1 outer_tick=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('return tree','return owner','return coverage','return destination','source seam','handler tail label','handler tail scheduler','handler tail legacy','handler tail tick','handler tail role','handler tail extent','handler tail shape','handler tail frame','resume dispatcher identity')
        print('V920_HANDLER_RETURN_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
