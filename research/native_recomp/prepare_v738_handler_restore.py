#!/usr/bin/env python3
"""Opt-in authenticated native restore alias at the handler epilogue."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v668_si_ack import geometry,HANDLER,shape
from prepare_v667_si_dispatch import exact
from prepare_owner_restore_v735 import plan
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
def patch_binding(s):
    a='#include "wii_si_handler_return_v725.h"'
    s=replace_exact(s,a,a+'\n#include "wii_gpr_restore_v736.h"\n#include "v738_private_restore_expectations.h"')
    a='inline thread_local SiHandlerReturnWitness witness(expected);'
    s=replace_exact(s,a,a+'\ninline thread_local GprRestoreWitness restore(restore_expected);\ninline bool restore_enabled(){const char* v=std::getenv("UNDERCOVER_V738_RESTORE");return v&&v[0]==\'1\'&&v[1]==\'\\0\';}')
    a='template<class C>void before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){'
    b=r'''[[noreturn]]inline void restore_reject(unsigned kind){
    std::cout<<"V738_RESTORE_INVALID kind="<<kind<<" witness="<<restore.failure()<<" stage="<<restore.stage()<<std::endl;std::_Exit(126);
}
inline void restore_event(unsigned stage){std::cout<<"V738_RESTORE_STAGE n="<<stage<<std::endl;}
template<class C>bool restore_observe(uint32_t a,C& c){
    if(restore.stage()!=1)return false;
    if(!held()||!restore.entry(c,a))restore_reject(2);
    restore_event(2);return true;
}
template<class C>void restore_before(C& c,uint32_t pc,uint32_t w){
    if(restore.stage()==0||restore.stage()==4)return;
    if(!held()||!si_completion_ack_trace.auxiliary_before()||!restore.before(c,pc,w))restore_reject(3);
}
'''
    s=replace_exact(s,a,b+a)
    a='    if(!witness.before(c,pc,w,held())){'
    b=r'''    if(restore.stage()>=1&&restore.stage()<=3){
        if(!held()||!restore.returned(c,pc)||!witness.restore_returned(c,pc,restore.visits(),held()))restore_reject(4);
        restore_event(3);
    }
    const bool allow=restore_enabled()&&pc==restore_expected.site&&w==restore_expected.branch&&
        ordinal==restore_ordinal&&kind==1&&restore.stage()==0;
    if(!witness.before(c,pc,w,held(),allow)){'''
    s=replace_exact(s,a,b)
    a='    if(witness.stage()==3)std::cout<<"V726_HANDLER_STAGE n=3"<<std::endl;'
    s=replace_exact(s,a,'    if(allow){if(!restore.start(c,pc,w,witness.entry_gprs()))restore_reject(1);restore_event(1);return;}\n'+a)
    return s
def patch_ack(s):
    a='if(v680::observe(a,c)||v688::observe(a,c))return;'
    return replace_exact(s,a,a+'if(v726::restore_observe(a,c))return;')

def render(site,root,branch,first,base,disp,ordinal=12):
    return ('#pragma once\n#include "wii_gpr_restore_v736.h"\nnamespace undercover::wii::v726 {\n'
        f'inline constexpr GprRestoreExpectation restore_expected{{0x{site:08x}u,0x{root:08x}u,0x{branch:08x}u,{first}u,{base}u,{disp}}};\n'
        f'inline constexpr unsigned restore_ordinal={ordinal}u;\n'+'}\n')
def patch_alias(s,root,code):
    body=exact_function(s,root)
    for i,w in enumerate(code):
        pc=root+4*i
        pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        if len(pat.findall(body))!=1:raise ValueError('restore label identity')
        body=pat.sub(lambda m:m[0]+f'    undercover::wii::v726::restore_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n',body,count=1)
    s=replace_exact(s,exact_function(s,root),body)
    inc='#include "undercover/wii_si_handler_return_binding_v726.h"'
    if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
    return s
def install(dol,elf,root,host):
    target,code,base,disp=plan(dol,elf)
    n,*_=geometry(dol,elf);words=exact(dol,elf,HANDLER,n)
    _,direct,indirect=shape(HANDLER,words)
    site=sorted([p for p,_ in direct]+list(indirect))[11]
    if dict(direct).get(site)!=target:raise ValueError('restore edge')
    branch=words[(site-HANDLER)//4]
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('private tree')
    expected={target+4*i:(target,w) for i,w in enumerate(code)}
    audit_native((p.read_text() for p in paths),main.read_text(),expected)
    changes={};calls=entries=0
    for p in paths:
        s=p.read_text()
        if owns_root(s,HANDLER):verify_direct(exact_function(s,HANDLER),site,target);calls+=1
        entries+=entry_count(s,target)
        if owns_root(s,target):changes[p]=patch_alias(s,target,code)
    if len(changes)!=1 or calls!=1 or entries!=1:raise ValueError('restore coverage')
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/'wii_gpr_restore_v736.h':(host/'wii_gpr_restore_v736.h').read_text(),
           dest/'v738_private_restore_expectations.h':render(site,target,branch,17,base,disp)}
    a=dest/'wii_si_ack_binding_v672.h';b=dest/'wii_si_handler_return_binding_v726.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() for p in (a,b)):raise ValueError('destination')
    files[a]=patch_ack(a.read_text());files[b]=patch_binding(b.read_text())
    for p,s in {**files,**changes}.items():p.write_text(s)
    print('V738_RESTORE_ROUTE installed=1 original_labels=16 direct_edges=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError) as e:
        allowed=('restore edge','private tree','restore label identity','restore coverage','destination','native IPC duplicate root','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge','helper exact root')
        print('V738_RESTORE_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
