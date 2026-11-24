#!/usr/bin/env python3
"""Authenticate original dispatcher dependencies and observe the actual SI indirect call."""
import argparse,hashlib,struct
from pathlib import Path
from prepare_v419_full_start import OWNER_SHA,MAX_DOL,words_at,direct_bl,replace_exact
from make_private_elf_symbol_map import ORIGINAL_SHA256,parse_functions
from audit_v264_osinit_retry_elf import read_words
from prepare_v625_ipc_client import audit_native
from prepare_v574_dsp_sc import diagnostic
DISPATCH=0x80526a3c
HANDLER=0x80531b34
SCHED=0x805293f8
TIME=0x8052a824
DISABLE=0x805265ac
RESTORE=0x805265d4
def exact(dol,elf,pc,n):
    w=words_at(dol,pc,n)
    if w!=tuple(read_words(elf,pc,n)):raise ValueError('word identity')
    return w
def calls(pc,words):
    return [(pc+4*i,direct_bl(w,pc+4*i),w) for i,w in enumerate(words) if w>>26==18 and w&3==1]
def route_geometry(dw,sw):
    if len(dw)!=0x2a4//4 or len(sw)!=0x3c//4:raise ValueError('dispatcher extent')
    d=calls(DISPATCH,dw);s=calls(SCHED,sw)
    head=[x for x in d if x[0] in (0x80526c80,0x80526c94)]
    if [(a,b) for a,b,_ in head]!=[(0x80526c80,TIME),(0x80526c94,SCHED)]:raise ValueError('dispatcher calls')
    if [x[1] for x in s]!=[DISABLE,RESTORE]:raise ValueError('scheduler calls')
    bctrl=[(DISPATCH+4*i,w) for i,w in enumerate(dw) if w==0x4e800421]
    if len(bctrl)!=1 or not 0x80526c98<=bctrl[0][0]<=0x80526ca8:raise ValueError('dispatcher indirect call')
    return head+s,bctrl[0]
def geometry(dol,elf):
    if hashlib.sha256(dol).hexdigest()!=OWNER_SHA or hashlib.sha256(elf).hexdigest()!=ORIGINAL_SHA256:raise ValueError('identity')
    sizes=parse_functions(elf)
    if sizes.get(DISPATCH)!=0x2a4 or sizes.get(SCHED)!=0x3c:raise ValueError('dispatcher extent')
    dw=exact(dol,elf,DISPATCH,0x2a4//4);sw=exact(dol,elf,SCHED,0x3c//4)
    edges,indirect=route_geometry(dw,sw)
    rows=[];expected={}
    for site,target,w in edges:
        if not sizes.get(target):raise ValueError('root')
        entry=exact(dol,elf,target,1)[0]
        rows.append((target,site+4,w,entry))
        expected[site]=(DISPATCH if site<SCHED else SCHED,w)
        expected[target]=(target,entry)
    if not sizes.get(HANDLER):raise ValueError('SI handler root')
    hw=exact(dol,elf,HANDLER,1)[0]
    expected[DISPATCH]=(DISPATCH,dw[0]);expected[HANDLER]=(HANDLER,hw)
    expected[indirect[0]]=(DISPATCH,indirect[1])
    return rows,indirect,hw,dw[0],expected
def render(rows,indirect,handler,dispatcher):
    fmt=lambda words:','.join(f'0x{w:08x}u' for w in words)
    return ('#pragma once\n#include "wii_si_dispatch_v667.h"\nnamespace undercover::wii::v667 {\n'
            'inline constexpr SiDispatchExpectations expected{std::array<SiDispatchEdge,4>{'
            +','.join('SiDispatchEdge{'+fmt(r)+'}' for r in rows)+'},'+fmt((*indirect,handler,dispatcher))+'};\n}\n')
BIND_INCLUDE='#include "v663_private_external_expectations.h"'
POLL='template<class C> bool poll(C& c){'
OBSERVE='template<class C> void observe(uint32_t a,C& c){'
END='''        std::cout<<"V663_EXTERNAL_RESULT vector=1 saved_context=1 dispatcher=1 si_pending=1 ack=0 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);'''
TRACE_INCLUDE='#include "wii_irq_bank_binding_v481.h"'
TRACE='''    void record(bool write,uint32_t address,unsigned width,uint32_t value,bool native)noexcept{
        if(!active_)return;'''
def patch_binding(s):
    for a,b in ((BIND_INCLUDE,BIND_INCLUDE+'\n#include "wii_si_dispatch_binding_v667.h"'),
                (POLL,POLL+'\n    if(v667::route.stage())return v667::poll(c);'),
                (OBSERVE,OBSERVE+'\n    if(v667::route.stage()){v667::observe(a,c);return;}'),
                (END,END.replace('std::_Exit(0);','if(v667::enabled()){v667::begin(c);return;}\n        std::_Exit(0);'))):
        s=replace_exact(s,a,b)
    return s
def patch_trace(s):
    s=replace_exact(s,TRACE_INCLUDE,TRACE_INCLUDE+'\n#include "wii_si_dispatch_v667.h"')
    return replace_exact(s,TRACE,TRACE.replace('        if(!active_)return;','        si_dispatch_pi_reads.record(write,address,width,value,native);\n        if(!active_)return;'))
def install(dol,elf,root,host):
    rows,indirect,handler,dispatcher,expected=geometry(dol,elf)
    shards=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('tree')
    native=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),expected)
    counts={r[0]:0 for r in rows};counts[HANDLER]=0
    for p in shards:
        s=p.read_text(encoding='utf-8')
        for pc in counts:counts[pc]+=s.count(f'if (nwii::runtime::g_trace_calls && ctx.pc == 0x{pc:X}) nwii::runtime::trace_call(0x{pc:X}, ctx);')
    if any(n!=1 for n in counts.values()):raise ValueError('trace coverage')
    dest=root/'nWiiRuntime/include/undercover'
    new={dest/name:(host/name).read_text(encoding='utf-8') for name in ('wii_si_dispatch_v667.h','wii_si_dispatch_binding_v667.h')}
    new[dest/'v667_private_si_dispatch_expectations.h']=render(rows,indirect,handler,dispatcher)
    binding=dest/'wii_external_entry_binding_v663.h';trace=dest/'wii_irq_return_witness_v482.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in new) or any(p.is_symlink() for p in (binding,trace)):raise ValueError('destination')
    new[binding]=patch_binding(binding.read_text(encoding='utf-8'))
    new[trace]=patch_trace(trace.read_text(encoding='utf-8'))
    for p,s in new.items():p.write_text(s,encoding='utf-8')
    return native
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        print(diagnostic(e));print('V667_SI_DISPATCH_ROUTE installed=0');return 1
    print(f'V667_SI_DISPATCH_ROUTE installed=1 native_labels={n} edges=4 indirect=1 ack=0 execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
