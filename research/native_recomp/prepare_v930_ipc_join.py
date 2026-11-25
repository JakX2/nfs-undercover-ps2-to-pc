#!/usr/bin/env python3
"""Opt-in original post-IRQ BL to IPC client entry, no IPC instruction executed."""
import argparse,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v928_leaf_finish import plan as leaf_plan
from make_v624_ipc_geometry import geometry,render,CALL,ROOT,SPANS
from prepare_v667_si_dispatch import exact
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count

def patch_binding(s):
    a='#include "v928_private_leaf_finish.h"'
    s=replace_exact(s,a,a+'\n#include "v624_private_ipc_expectations.h"\n#include "v930_private_ipc_join.h"')
    a='inline thread_local IrqLeafFinishWitness finish(finish_expected);'
    s=replace_exact(s,a,a+'''
inline thread_local IpcClientWitness ipc(v624::expected_client);
inline thread_local IpcEntryJoinWitness ipc_join(ipc_join_expected);
[[noreturn]]inline void reject_ipc(unsigned kind){
    std::cout<<std::dec<<"V930_IPC_INVALID kind="<<kind<<" ipc="<<ipc.failure()
        <<" join="<<ipc_join.failure()<<" stage="<<ipc.stage()<<" refusal="<<ipc.entry_refusal()<<std::endl;std::_Exit(126);
}
''')
    a='    if(finish.stage()){\n        if(!advance(c,true)||!finish.dispatch(c,pc,true))reject_finish(4);'
    s=replace_exact(s,a,'''    if(ipc_join.stage()==1u){
        if(!ipc_join.entry(c,pc,v850::held(c))||!ipc.observe(pc,c)||ipc.stage()!=2u)reject_ipc(3);
        std::cout<<"V930_IPC_ENTRY original_bl=1 original_target=1 cold_prerequisites=1 same_tick=1 device_held=1 ipc_instruction_executed=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
    if(finish.stage()){
        if(!advance(c,true)||!finish.dispatch(c,pc,true))reject_finish(4);
        // At the V616 pre-label trace, before the caller's real tick.
        // Reuse the original V623 cold heap/table/transport checks.
        if(!ipc.begin(c))reject_ipc(1);''')
    a='    std::cout<<"V928_LEAF_RETURN original_leaf=1 original_blr=1 osinit_resume=1 previous_ee=0 integer_state=1 gqr=1 device_held=1 caller_instruction_executed=0 boot_verified=0"<<std::endl;\n    std::_Exit(0);'
    return replace_exact(s,a,a.replace('std::_Exit(0);','''if(ipc.stage()!=1u||!ipc_join.start(c,pc,w,finish.stage()==5u,v850::held(c)))reject_ipc(2);
    std::cout<<"V930_IPC_BEGIN cold_prerequisites=1 original_call=1"<<std::endl;'''))

def install(dol,elf,root,host):
    _,_,caller,cw=leaf_plan(dol,elf)
    g=geometry(dol,elf);rows,_,_,_=g
    if rows[0][:3]!=(ROOT,CALL+4,cw):raise ValueError('IPC call identity')
    n=dict(SPANS).get(ROOT)
    if n!=0xb4:raise ValueError('IPC extent')
    code=exact(dol,elf,ROOT,n//4)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):
        raise ValueError('IPC tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    expected={CALL:(caller,cw),**{ROOT+4*i:(ROOT,w) for i,w in enumerate(code)}}
    if audit_native(src.values(),outer,expected)!=len(expected):raise ValueError('IPC coverage')
    owned=[exact_function(s,caller) for s in src.values() if owns_root(s,caller)]
    if len(owned)!=1 or sum(entry_count(s,ROOT) for s in src.values())!=1:raise ValueError('IPC owner')
    verify_direct(owned[0],CALL,ROOT)
    dest=root/'nWiiRuntime/include/undercover';binding=dest/'wii_live_irq_return_binding_v922.h'
    vals=','.join(f'0x{x:08x}u' for x in (CALL,ROOT,cw,code[0]))
    files={dest/'v624_private_ipc_expectations.h':render(*g),
        dest/'v930_private_ipc_join.h':'#pragma once\n#include "wii_ipc_entry_join_v930.h"\nnamespace undercover::wii::v922 {inline constexpr IpcEntryJoinExpectation ipc_join_expected{'+vals+'};}\n'}
    for name in ('wii_ipc_client_witness_v623.h','wii_ipc_entry_join_v930.h'):
        files[dest/name]=(host/name).read_text()
    if dest.is_symlink() or binding.is_symlink() or not binding.is_file() or any(p.exists() or p.is_symlink() for p in files):
        raise ValueError('IPC destination')
    files[binding]=patch_binding(binding.read_text())
    for p,s in files.items():p.write_text(s)
    print('V930_IPC_ROUTE installed=1 original_call=1 root_labels=45 cold_witness=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        safe=('IPC call identity','IPC extent','IPC tree','IPC coverage','IPC owner','IPC destination','source seam','native IPC label identity','native IPC coverage','native IPC dispatch','native IPC label body','native IPC duplicate root','helper direct native call','helper native return edge')
        print('V930_IPC_ROUTE installed=0 reason='+ (str(e).replace(' ','_') if str(e) in safe else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
