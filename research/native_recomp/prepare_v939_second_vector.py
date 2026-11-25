#!/usr/bin/env python3
"""Privately authenticate the second original vector/trampoline continuation."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from audit_v662_external_overlay import expected as vector_words
from prepare_v663_external_entry import TRAMP,DISPATCH
from prepare_v667_si_dispatch import exact
from make_private_elf_symbol_map import parse_functions
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v850_callback_return import BLOCK_END,INSTR_PREFIX
from prepare_v807_callback_prefix import SI
V=0x80000500
def patch_label(body,pc,w):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('second vector label')
    pos=hits[0].end();end=BLOCK_END.search(body,pos);stop=end.start() if end else len(body)
    block=body[pos:stop]
    if block.count(SI)!=1 or not INSTR_PREFIX.fullmatch(block[:block.index(SI)]) or 'v922::second_before' in block:
        raise ValueError('second vector scheduler')
    off=pos+block.index(SI)+len(SI)
    return body[:off]+f'    undercover::wii::v922::second_before(ctx,0x{pc:08x}u,0x{w:08x}u);\n'+body[off:]
def patch_binding(s):
    a='#include "wii_pending_external_reentry_v932.h"'
    s=replace_exact(s,a,a+'\n#include "v939_private_second_vector.h"')
    a='inline thread_local PendingExternalReentry reentry;'
    s=replace_exact(s,a,a+'''
inline thread_local SecondVectorWitness second(second_expected);
inline bool second_enabled(){const char* v=std::getenv("UNDERCOVER_V939_SECOND_VECTOR");return v&&v[0]=='1'&&v[1]=='\\0';}
[[noreturn]]inline void reject_second(unsigned k){
    std::cout<<std::dec<<"V939_SECOND_INVALID kind="<<k<<" reason="<<second.failure()<<" stage="<<second.stage()
        <<" vector="<<second.vector_visits()<<" trampoline="<<second.trampoline_visits()
        <<" gpr_mask="<<second.gpr_mask()<<" special_mask="<<second.special_mask()<<std::endl;
    std::_Exit(126);
}
''')
    a='template<class C>void before(C& c,uint32_t pc,uint32_t w){'
    s=replace_exact(s,a,'''template<class C>void second_before(C& c,uint32_t pc,uint32_t w){
    if(!second.stage())return;
    if(!advance(c)||!second.before(c,pc,w,cause(),mask(),v850::held(c)))reject_second(1);
}
'''+a)
    a='    if(reentry.stage()){\n        if(!reentry.outer_poll'
    s=replace_exact(s,a,'''    if(second.stage()){
        if(!second.poll(c,cause(),mask(),v850::held(c)))reject_second(2);
        return false;
    }
'''+a)
    a='    if(reentry.stage()){\n        if(!advance(c,true)||!reentry.vector_entry'
    s=replace_exact(s,a,'''    if(second.stage()){
        if(c.inst_count==second.last_tick()+1u){
            if(!advance(c,true))reject_second(3);
        }else if(c.inst_count!=second.last_tick()||!v850::held(c))reject_second(3);
        if(!second.entry(c,pc,cause(),mask(),v850::held(c)))reject_second(3);
        if(second.stage()==2u)std::cout<<"V939_SECOND_TRAMPOLINE original_vector=1 partial_context=1"<<std::endl;
        if(second.stage()==3u){
            std::cout<<std::dec<<"V939_SECOND_RESULT original_vector=1 original_trampoline=1 saved_fields=38 vector_visits="
                <<second.vector_visits()<<" trampoline_visits="<<second.trampoline_visits()
                <<" second_dispatcher_entry=1 device_held=1 dispatcher_instruction_executed=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }
'''+a)
    a='            <<route.visits()<<" device_held=1 resumed_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);'
    s=replace_exact(s,a,a.replace('std::_Exit(0);','')+'''
        if(!second_enabled())std::_Exit(0);
        if(!second.begin(c,reentry,cause(),mask(),v850::held(c)))reject_second(4);
        return;''')
    return s
def install(dol,elf,root,host):
    v=vector_words(dol)
    if parse_functions(elf).get(TRAMP)!=80:raise ValueError('second trampoline extent')
    t=exact(dol,elf,TRAMP,20);dw=exact(dol,elf,DISPATCH,1)[0]
    expected={V+4*i:(V,w) for i,w in enumerate(v)}
    expected.update({TRAMP+4*i:(TRAMP,w) for i,w in enumerate(t)})
    expected[DISPATCH]=(DISPATCH,dw)
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('second vector tree')
    src={p:p.read_text() for p in paths};outer=main.read_text()
    if audit_native(src.values(),outer,expected)!=59:raise ValueError('second vector coverage')
    if any(sum(entry_count(s,a) for s in src.values())!=1 for a in (V,TRAMP,DISPATCH)):raise ValueError('second vector entries')
    changes={}
    for a,ws in ((V,v),(TRAMP,t)):
        owners=[p for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1:raise ValueError('second vector owner')
        p=owners[0];s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        for i,w in enumerate(ws):out=patch_label(out,a+4*i,w)
        s=replace_exact(s,body,out)
        inc='#include "undercover/wii_live_irq_return_binding_v922.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s
    dest=root/'nWiiRuntime/include/undercover';binding=dest/'wii_live_irq_return_binding_v922.h'
    names=(dest/'wii_second_vector_v939.h',dest/'v939_private_second_vector.h')
    if dest.is_symlink() or binding.is_symlink() or not binding.is_file() or any(p.exists() or p.is_symlink() for p in names):raise ValueError('second vector destination')
    fmt=lambda ws:','.join(f'0x{w:08x}u' for w in ws)
    private='#pragma once\n#include "wii_second_vector_v939.h"\nnamespace undercover::wii::v922 {\n'
    private+='inline constexpr std::array<uint32_t,38> second_vector_words{'+fmt(v)+'};\n'
    private+='inline constexpr std::array<uint32_t,20> second_trampoline_words{'+fmt(t)+'};\n'
    private+='inline constexpr SecondVectorExpectation second_expected{'+fmt((TRAMP,DISPATCH,0x806f5318,dw))+',second_vector_words,second_trampoline_words};\n}\n'
    for p,s in {**changes,names[0]:(host/names[0].name).read_text(),names[1]:private,binding:patch_binding(binding.read_text())}.items():p.write_text(s)
    print('V939_SECOND_ROUTE installed=1 vector_labels=38 trampoline_labels=20 dispatcher_entry=1 execution=0')
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allowed=('second vector label','second vector scheduler','second trampoline extent','second vector tree','second vector coverage','second vector entries','second vector owner','second vector destination','source seam','native IPC label identity','native IPC coverage','native IPC dispatch','native IPC label body','helper exact root')
        print('V939_SECOND_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
