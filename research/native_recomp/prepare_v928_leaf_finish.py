#!/usr/bin/env python3
"""Authenticate original post-RFI interrupt-enable BLR and OSInit caller."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v616_irq_enable import ENTRY,RETURN,expectations
from prepare_v667_si_dispatch import exact
from prepare_owner_irq_finish_v927 import extract_shape
from make_private_elf_symbol_map import parse_functions
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root
from prepare_v726_handler_return import verify_resume_dispatch
from prepare_v922_irq_return import patch_label

def plan(dol,elf):
    _,resume,labels=expectations(dol,elf)
    leaf=exact(dol,elf,resume,2)
    if resume!=ENTRY+12 or leaf[-1]!=0x4e800020 or not extract_shape(leaf[0]):raise ValueError('IRQ leaf shape')
    owners=[pc for pc,n in parse_functions(elf).items() if pc<=RETURN-4 and RETURN<pc+n]
    if len(owners)!=1 or owners[0]==ENTRY:raise ValueError('caller owner')
    return resume,leaf,owners[0],labels[RETURN]

def patch_one(body,pc,w,caller=False):
    out=patch_label(body,pc,w,caller)
    old=f'    undercover::wii::v922::{"resume" if caller else "before"}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    new=f'    undercover::wii::v922::{"caller_resume" if caller else "leaf_blr"}(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    return replace_exact(out,old,new)

def patch_binding(s):
    a='#include "v922_private_irq_return.h"'
    s=replace_exact(s,a,a+'\n#include "v928_private_leaf_finish.h"')
    a='inline thread_local bool dispatch_seen=false;'
    s=replace_exact(s,a,a+'''
inline thread_local IrqLeafFinishWitness finish(finish_expected);
[[noreturn]]inline void reject_finish(unsigned kind){
    std::cout<<std::dec<<"V928_LEAF_INVALID kind="<<kind<<" reason="<<finish.failure()
             <<" stage="<<finish.stage()<<std::endl;std::_Exit(126);
}
''')
    a='    const unsigned prior=route.stage();'
    s=replace_exact(s,a,'''    if(finish.stage()){
        if(!v850::held(c)||!finish.poll(c,true))reject_finish(3);
        std::cout<<"V928_LEAF_POLL original_blr=1 same_tick=1"<<std::endl;
        return false;
    }
'''+a)
    a='    if(route.stage()==4u){'
    s=replace_exact(s,a,'''    if(finish.stage()){
        if(!advance(c,true)||!finish.dispatch(c,pc,true))reject_finish(4);
        return;
    }
'''+a)
    a='<<route.visits()<<" device_held=1 resumed_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    s=replace_exact(s,a,a.replace('std::_Exit(0);','')+'''
    auto* captured=v921::join.captured();
    // V663 authenticated that the pre-enable MSR had EE clear.
    if(!captured||!finish.start(c,*captured,false,pc,w,v850::held(c)))reject_finish(1);
    std::cout<<"V928_LEAF_BEGIN original_resume=1 previous_ee=0"<<std::endl;''')
    a='template<class C>void resume(C& c,uint32_t pc,uint32_t w){'
    return replace_exact(s,a,'''template<class C>void leaf_blr(C& c,uint32_t pc,uint32_t w){
    if(!finish.stage())return;
    if(!advance(c)||!finish.before_blr(c,pc,w,true))reject_finish(2);
    std::cout<<"V928_LEAF_BLR original_extract=1 previous_ee=0"<<std::endl;
}
template<class C>void caller_resume(C& c,uint32_t pc,uint32_t w){
    if(!finish.stage())return;
    if(!advance(c)||!finish.returned(c,pc,w,true))reject_finish(5);
    std::cout<<"V928_LEAF_RETURN original_leaf=1 original_blr=1 osinit_resume=1 previous_ee=0 integer_state=1 gqr=1 device_held=1 caller_instruction_executed=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
'''+a)

def install(dol,elf,root,host):
    resume,leaf,caller,cw=plan(dol,elf)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('private tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    verify_resume_dispatch(outer,caller,RETURN)
    verify_resume_dispatch(outer,ENTRY,resume)
    expected={resume:(ENTRY,leaf[0]),resume+4:(ENTRY,leaf[1]),RETURN:(caller,cw)}
    if audit_native(src.values(),outer,expected)!=3:raise ValueError('leaf coverage')
    changes={}
    for rootpc,pc,w,is_caller in ((ENTRY,resume+4,leaf[1],False),(caller,RETURN,cw,True)):
        owned=[p for p,s in src.items() if owns_root(s,rootpc)]
        if len(owned)!=1:raise ValueError('leaf owner')
        p=owned[0];s=changes.get(p,src[p]);body=exact_function(s,rootpc)
        out=patch_one(body,pc,w,is_caller);s=replace_exact(s,body,out)
        inc='#include "undercover/wii_live_irq_return_binding_v922.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover'
    binding=dest/'wii_live_irq_return_binding_v922.h'
    files={dest/'wii_irq_leaf_finish_v927.h':(host/'wii_irq_leaf_finish_v927.h').read_text()}
    vals=','.join(f'0x{v:08x}u' for v in (resume,leaf[0],RETURN,cw))
    files[dest/'v928_private_leaf_finish.h']='#pragma once\n#include "wii_irq_leaf_finish_v927.h"\nnamespace undercover::wii::v922 {inline constexpr IrqLeafFinishExpectation finish_expected{'+vals+'};}\n'
    if dest.is_symlink() or binding.is_symlink() or not binding.is_file() or any(p.exists() or p.is_symlink() for p in files):
        raise ValueError('leaf destination')
    files[binding]=patch_binding(binding.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print('V928_LEAF_ROUTE installed=1 original_resume_labels=2 osinit_resume=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('IRQ leaf shape','caller owner','private tree','leaf coverage','leaf owner','leaf destination','source seam','IRQ return label','IRQ return tick','IRQ return scheduler','resume dispatcher identity','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch')
        print('V928_LEAF_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
