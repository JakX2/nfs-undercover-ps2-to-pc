#!/usr/bin/env python3
"""Install a bounded first original SI handler ACK lane, private generated tree only."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,words_at,replace_exact
from prepare_v668_si_ack import geometry,shape,HANDLER,patch_binding as patch_device
from prepare_v625_ipc_client import DEF,LABEL,audit_native
from prepare_v574_dsp_sc import diagnostic
INCLUDE='#include "v667_private_si_dispatch_expectations.h"'
POLL='template<class C>bool poll(C& c){'
OBSERVE='template<class C>void observe(uint32_t a,C& c){'
END='''        std::cout<<"V667_SI_DISPATCH_RESULT pi_reads=1 timebase=1 scheduler_disable=1 handler=1 index=20 si_pending=1 ack=0 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);'''
BIND='    static bool active()noexcept{return active_!=nullptr;}'
SHARD_INCLUDE='#include "runtime/cpu_context.h"'
def patch_dispatch(s):
    for a,b in ((INCLUDE,INCLUDE+'\n#include "wii_si_ack_binding_v672.h"'),
                (POLL,POLL+'\n    if(v672::active())return v672::poll(c);'),
                (OBSERVE,OBSERVE+'\n    if(v672::active()){v672::observe(a,c);return;}'),
                (END,END.replace('std::_Exit(0);','if(v672::enabled()){v672::begin(c);return;}\n        std::_Exit(0);'))):
        s=replace_exact(s,a,b)
    return s
def patch_si(s):
    s=patch_device(s)
    # Inactive writes retain the existing exception behaviour. An armed
    # write rejection has a bounded public diagnostic and must stop.
    s=replace_exact(s,'#include "wii_si_completion_ack_v668.h"','#include "wii_si_completion_ack_v668.h"\n#include <cstdlib>\n#include <iostream>')
    s=replace_exact(s,'si_completion_ack_trace.write(active_->controller_,*off,value);','''try{si_completion_ack_trace.write(active_->controller_,*off,value);}
        catch(const std::exception&){
            if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Idle)throw;
            const auto pc=si_completion_ack_trace.post_control();
            if(pc.kind)std::cout<<"V711_POST_CONTROL kind="<<pc.kind<<" channel="<<pc.channel
                <<" geometry="<<pc.geometry<<" type="<<pc.type<<" mask="<<pc.mask<<" reserved="<<pc.reserved<<std::endl;
            std::cout<<"V677_SI_ACK_WRITE_INVALID trace="<<si_completion_ack_trace.failure()<<std::endl;
            std::_Exit(126);
        }''')
    # The pre-existing sampling/discovery composition may already use a
    # local readback variable. Preserve it and both earlier observers.
    raw='return active_->controller_.read(*off);'
    observed='const auto value=active_->controller_.read(*off);'
    if s.count(raw)+s.count(observed)!=1:raise ValueError('SI ACK read seam')
    s=replace_exact(s,raw if raw in s else observed,'''return checked_read(*off);''' if raw in s else '''const auto value=checked_read(*off);''')
    check='            throw std::runtime_error("SI unsupported access");'
    s=replace_exact(s,check,'''        {
            if(si_completion_ack_trace.phase()!=SiCompletionAckTrace::Phase::Idle){
                std::cout<<"V697_SI_ACCESS_INVALID width="<<width<<" integer="<<unsigned(integer)<<std::endl;
                std::_Exit(126);
            }
            throw std::runtime_error("SI unsupported access");
        }''')
    s=replace_exact(s,BIND,BIND+'''
    static uint32_t checked_read(unsigned off){
        try{return si_completion_ack_trace.read(active_->controller_,off);}
        catch(const std::exception&){
            if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Idle)throw;
            std::cout<<"V697_SI_READ_INVALID trace="<<si_completion_ack_trace.failure()<<std::endl;
            std::_Exit(126);
        }
    }''')
    return replace_exact(s,BIND,BIND+'''
    static bool arm_completion_ack(const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
                                   const uint64_t& tick,uint32_t first,uint32_t end){
        return active_&&si_completion_ack_trace.arm(active_->controller_,cause,mask,tick,first,end);
    }''')
def call_census(root,words):
    _,direct,indirect=shape(root,words)
    routes=sorted([(pc,1) for pc,_ in direct]+[(pc,2) for pc in indirect])
    if len(routes)>32 or len({pc for pc,_ in routes})!=len(routes):raise ValueError('SI ACK call census')
    return {pc:(i+1,kind) for i,(pc,kind) in enumerate(routes)}
def patch_shard(s,words,root=HANDLER):
    # Match one exact original function. Every observed label is authenticated
    # against DOL/ELF before the private source is modified.
    fs=list(DEF.finditer(s));hits=[i for i,f in enumerate(fs) if int(f[1].split('_')[1],16)==root]
    if not hits:return s,{}
    if len(hits)!=1:raise ValueError('SI ACK duplicate root')
    i=hits[0];lo=fs[i].end();hi=fs[i+1].start() if i+1<len(fs) else len(s)
    body=s[lo:hi];labels=list(LABEL.finditer(body));seen={}
    for l in labels:
        pc=int(l[1],16)
        if pc in seen or pc<root or (pc-root)%4 or pc>=root+4*len(words) or int(l[2],16)!=pc or int(l[3],16)!=words[(pc-root)//4]:
            raise ValueError('SI ACK label identity')
        seen[pc]=(root,int(l[3],16))
    if root not in seen:raise ValueError('SI ACK root coverage')
    stores,_,_=shape(root,words)
    calls=call_census(root,words)
    if any(pc not in seen or pc+4 not in seen for pc in stores):raise ValueError('SI ACK store successor coverage')
    # All emitted handler labels must have real native instruction bodies.
    for pc in sorted(seen,reverse=True):
        w=seen[pc][1]
        pattern=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n    \+\+ctx\.inst_count;\n')
        m=list(pattern.finditer(body))
        if len(m)!=1:raise ValueError('SI ACK label tick')
        pos=m[0].end()
        ordinal,kind=calls.get(pc,(0,0))
        body=body[:pos]+f'    undercover::wii::v672::before(ctx,0x{pc:08x}u,0x{w:08x}u,{ordinal}u,{kind}u);\n'+body[pos:]
    out=replace_exact(s[:lo]+body+s[hi:],SHARD_INCLUDE,SHARD_INCLUDE+'\n#include "undercover/wii_si_ack_binding_v672.h"')
    return out,seen
def install(dol,elf,root,host):
    n,stores,_,_,_=geometry(dol,elf);words=words_at(dol,HANDLER,n)
    shards=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(shards)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in shards+[main]):raise ValueError('tree')
    changes={};expected={}
    for p in shards:
        s=p.read_text(encoding='utf-8')
        if not re.search(r'(?mi)^void (?:fn|func)_80531b34\(CPUContext& ctx\) \{',s):continue
        out,seen=patch_shard(s,words)
        if expected or not seen:raise ValueError('SI ACK unique root')
        changes[p]=out;expected=seen
    if not expected:raise ValueError('SI ACK root coverage')
    native=audit_native((p.read_text(encoding='utf-8') for p in shards),main.read_text(encoding='utf-8'),expected)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/name:(host/name).read_text(encoding='utf-8') for name in ('wii_si_completion_ack_v668.h','wii_si_ack_binding_v672.h')}
    files[dest/'v672_private_si_ack_expectations.h']=('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v672 {\n'
        f'inline constexpr uint32_t handler_first=0x{HANDLER:08x}u,handler_end=0x{HANDLER+4*n:08x}u;\n'+'}\n')
    dispatch=dest/'wii_si_dispatch_binding_v667.h';si=dest/'wii_si_binding_v512.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() for p in (dispatch,si)):raise ValueError('destination')
    files[dispatch]=patch_dispatch(dispatch.read_text(encoding='utf-8'))
    files[si]=patch_si(si.read_text(encoding='utf-8'))
    for p,s in {**changes,**files}.items():p.write_text(s,encoding='utf-8')
    return native,stores
def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        n,stores=install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,struct.error,UnicodeError) as e:
        print(diagnostic(e));print('V672_SI_ACK_ROUTE installed=0');return 1
    print(f'V672_SI_ACK_ROUTE installed=1 native_labels={n} store_candidates={stores} handler_only=1 execution=0');return 0
if __name__=='__main__':raise SystemExit(main())
