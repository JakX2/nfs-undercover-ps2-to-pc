#!/usr/bin/env python3
"""Connect the verified V947 second-dispatch path to the full original image."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_v667_si_dispatch import exact,DISPATCH,HANDLER,TIME,SCHED,DISABLE,RESTORE
from prepare_owner_second_dispatch_v946 import plan,reachable
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v850_callback_return import BLOCK_END,INSTR_PREFIX
from prepare_v807_callback_prefix import SI

def patch_label(body,pc,w,root,guard):
    # Refuse unexpected instrumentation, including a missing V922 hook
    # on the shared OSDisable/OSRestore roots.
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('second dispatcher label')
    m=hits[0];tail=body[m.end():]
    tick=re.match(r'(?:    if \(nwii::runtime::g_trace_calls\) nwii::runtime::trace_call\(0x[0-9A-F]+, ctx\); // V[0-9]+ [^\n]+\n)?    \+\+ctx\.inst_count;\n',tail)
    if not tick:raise ValueError('second dispatcher tick')
    pos=m.end()+tick.end();end=BLOCK_END.search(body,pos);stop=end.start() if end else len(body)
    block=body[pos:stop]
    if block.count(SI)!=1 or not INSTR_PREFIX.fullmatch(block[:block.index(SI)]):
        raise ValueError('second dispatcher scheduler')
    existing=f'    undercover::wii::v922::before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'
    if root in (DISABLE,RESTORE):
        if guard or block.count(existing)!=1:raise ValueError('second dispatcher shared')
        return body
    if existing in block or 'v922::second_dispatch_before' in block:raise ValueError('second dispatcher shared')
    if root==TIME:
        old=f'    undercover::wii::v709::before(ctx,0x{pc:08x}u,0x{w:08x}u,2u);\n'
        if block.count(old)!=1:raise ValueError('second dispatcher time')
        block=replace_exact(block,old,'    if(!undercover::wii::v922::second_dispatch_active_now()) '+old.lstrip())
    i=block.index(SI)+len(SI)
    block=block[:i]+f'    undercover::wii::v922::second_dispatch_before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(guard).lower()});\n'+block[i:]
    return body[:pos]+block+body[stop:]

def patch_binding(s):
    a='#include "v939_private_second_vector.h"'
    s=replace_exact(s,a,a+'\n#include "wii_second_si_dispatch_v944.h"\n#include "v667_private_si_dispatch_expectations.h"')
    a='inline thread_local SecondVectorWitness second(second_expected);'
    s=replace_exact(s,a,a+'''
inline thread_local SecondSiDispatchWitness second_dispatch(v667::expected);
inline thread_local uint64_t dispatch_last=0;
inline thread_local unsigned dispatch_visits=0;
inline bool second_dispatch_enabled(){const char* v=std::getenv("UNDERCOVER_V951_SECOND_DISPATCH");return v&&v[0]=='1'&&v[1]=='\\0';}
inline bool second_dispatch_active_now(){return second_dispatch.stage()>=1u&&second_dispatch.stage()<=5u;}
[[noreturn]]inline void reject_dispatch(unsigned kind){
    std::cout<<std::dec<<"V951_DISPATCH_INVALID kind="<<kind<<" stage="<<second_dispatch.stage()
        <<" reason="<<second_dispatch.failure()<<" visits="<<dispatch_visits<<std::endl;
    std::_Exit(126);
}
''')
    a='template<class C>void begin(C& c,uint32_t pc,uint32_t w){'
    s=replace_exact(s,a,'''template<class C>void second_dispatch_before(C& c,uint32_t pc,uint32_t w,bool guard=false){
    if(!second_dispatch_active_now())return;
    if(guard||c.inst_count-dispatch_last!=1u||++dispatch_visits>2048u||
       !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w||
       !advance(c)||!second_dispatch.poll(c,cause(),mask(),v850::held(c)))reject_dispatch(1);
    dispatch_last=c.inst_count;
}
template<class C>void second_dispatch_observe(uint32_t pc,C& c){
    if(c.inst_count==dispatch_last+1u){
        if(!advance(c,true))reject_dispatch(2);
        dispatch_last=c.inst_count;
    }else if(c.inst_count!=dispatch_last||!v850::held(c))reject_dispatch(2);
    if(!second_dispatch.observe(c,pc,cause(),mask(),v850::held(c)))reject_dispatch(2);
    std::cout<<std::dec<<"V951_DISPATCH_EDGE n="<<second_dispatch.stage()-1u<<std::endl;
    if(second_dispatch.stage()==6u){
        second_dispatch_mmio=nullptr;
        std::cout<<std::dec<<"V951_DISPATCH_RESULT original_dispatcher=1 original_leaves=4 pi_reads=1 handler_entry=1 saved_fields=38 visits="
            <<dispatch_visits<<" device_held=1 handler_instruction_executed=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
'''+a)
    a='template<class C>void before(C& c,uint32_t pc,uint32_t w){\n    if(!active())return;'
    s=replace_exact(s,a,a+'\n    if(second_dispatch_active_now()){second_dispatch_before(c,pc,w);return;}')
    a='template<class C>bool poll(C& c){'
    s=replace_exact(s,a,a+'''
    if(second_dispatch_active_now()){
        if(c.inst_count!=dispatch_last||!second_dispatch.poll(c,cause(),mask(),v850::held(c)))reject_dispatch(3);
        return false;
    }''')
    a='template<class C>void observe(uint32_t pc,C& c){'
    s=replace_exact(s,a,a+'\n    if(second_dispatch_active_now()){second_dispatch_observe(pc,c);return;}')
    a='''                <<" second_dispatcher_entry=1 device_held=1 dispatcher_instruction_executed=0 boot_verified=0"<<std::endl;
            std::_Exit(0);'''
    s=replace_exact(s,a,a.replace('std::_Exit(0);','''if(!second_dispatch_enabled())std::_Exit(0);
            if(second_dispatch_mmio||!second_dispatch.begin(c,reentry.captured(),cause(),mask(),v850::held(c)))reject_dispatch(4);
            second_dispatch_mmio=&second_dispatch;dispatch_last=c.inst_count;
            std::cout<<"V951_DISPATCH_BEGIN captured_context=1 held_token=1"<<std::endl;'''))
    return s

def patch_trace(s):
    a='#include "wii_si_dispatch_v667.h"'
    s=replace_exact(s,a,a+'\n#include "wii_second_si_dispatch_v944.h"')
    a='        si_dispatch_pi_reads.record(write,address,width,value,native);'
    return replace_exact(s,a,a+'\n        record_second_dispatch_pi(write,address,width,value,native);')

def install(dol,elf,root,host):
    roots,edges,indirect,_,hw,_,guard=plan(dol,elf)
    original={a:exact(dol,elf,a,len(ws)) for a,ws in roots.items() if a!=HANDLER}
    expected={pc:(a,original[a][(pc-a)//4]) for a,ws in roots.items() if a!=HANDLER for pc in reachable(a,ws,guard,indirect)}
    expected[HANDLER]=(HANDLER,hw)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('second dispatcher tree')
    src={p:p.read_text() for p in paths}
    if audit_native(src.values(),main.read_text(),expected)!=len(expected):raise ValueError('second dispatcher coverage')
    if any(sum(entry_count(s,a) for s in src.values())!=1 for a in roots):raise ValueError('second dispatcher entry')
    changes={}
    for a in original:
        owners=[p for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1:raise ValueError('second dispatcher owner')
        p=owners[0];s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        for pc,(owner,w) in expected.items():
            if owner==a:out=patch_label(out,pc,w,a,pc in guard)
        for dst,lr,_,_ in edges:
            if (a==DISPATCH and lr-4<SCHED) or (a==SCHED and lr-4>=SCHED):verify_direct(out,lr-4,dst)
        if out!=body:s=replace_exact(s,body,out)
        inc='#include "undercover/wii_live_irq_return_binding_v922.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover';binding=dest/'wii_live_irq_return_binding_v922.h';trace=dest/'wii_irq_return_witness_v482.h';header=dest/'wii_second_si_dispatch_v944.h'
    if dest.is_symlink() or header.exists() or header.is_symlink() or any(p.is_symlink() or not p.is_file() for p in (binding,trace)):raise ValueError('second dispatcher destination')
    for p,s in {**changes,header:(host/header.name).read_text(),binding:patch_binding(binding.read_text()),trace:patch_trace(trace.read_text())}.items():p.write_text(s)
    print(f'V951_DISPATCH_ROUTE installed=1 native_labels={len(expected)} original_edges=4 indirect=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allowed=('second dispatcher label','second dispatcher tick','second dispatcher scheduler','second dispatcher shared','second dispatcher time','second dispatcher tree','second dispatcher coverage','second dispatcher entry','second dispatcher owner','second dispatcher destination','source seam','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V951_DISPATCH_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
