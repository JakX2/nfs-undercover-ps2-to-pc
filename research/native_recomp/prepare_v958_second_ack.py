#!/usr/bin/env python3
"""Privately compose original second-handler labels and exclusive SI handoff."""
import argparse,re,struct
from pathlib import Path
from prepare_v419_full_start import MAX_DOL,replace_exact
from prepare_owner_second_ack_v955 import plan
from prepare_owner_second_dispatch_v946 import reachable
from prepare_v667_si_dispatch import HANDLER,exact
from prepare_v625_ipc_client import audit_native
from prepare_v680_si_helper import exact_function,verify_direct
from prepare_v709_os_leaves import owns_root,entry_count
from prepare_v850_callback_return import BLOCK_END
from prepare_v807_callback_prefix import SI

def patch_label(body,pc,w,legacy,guard):
    pat=re.compile(r'(?mi)^loc_'+f'{pc:X}'+r': ;\n    // 0x'+f'{pc:08X}: {w:08X}'+r'\n')
    hits=list(pat.finditer(body))
    if len(hits)!=1:raise ValueError('second ACK label')
    pos=hits[0].end()
    stop=BLOCK_END.search(body,pos);end=stop.start() if stop else len(body)
    block=body[pos:end]
    old=re.compile(r'(?m)^    undercover::wii::'+legacy+r'::before\(ctx,0x'+f'{pc:08x}'+r'u,0x'+f'{w:08x}'+r'u(?:,[0-9]+u,[0-9]+u)?\);\n')
    found=list(old.finditer(block))
    if len(found)!=1 or block.count(SI)!=1 or block.count('++ctx.inst_count;')!=1 or 'v958::' in block:
        raise ValueError('second ACK hook')
    # Require tick before both observers and scheduler. Preserve legacy order,
    # including the pre-tick trace at any later handler resume label.
    tick=block.index('++ctx.inst_count;')
    if tick>block.index(SI) or tick>found[0].start():raise ValueError('second ACK tick')
    block=old.sub(lambda m:'    if(!undercover::wii::v958::active()) '+m[0].lstrip(),block,count=1)
    i=block.index(SI)+len(SI)
    block=block[:i]+f'    undercover::wii::v958::before(ctx,0x{pc:08x}u,0x{w:08x}u,{str(guard).lower()});\n'+block[i:]
    return body[:pos]+block+body[end:]

def patch_si(s):
    a='#include "wii_postack_transfer_device_v771.h"'
    s=replace_exact(s,a,a+'\n#include "wii_second_ack_live_v958.h"')
    a='    static bool active()noexcept{return active_!=nullptr;}'
    s=replace_exact(s,a,a+'''
    static bool handoff_second_ack(const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,const uint64_t& tick){
        return active_&&si_transfer_device.handoff_second_ack(v958::ack,active_->controller_,cause,mask,tick);
    }
#ifdef UNDERCOVER_V1025_PRIVATE_TRANSFER
    // Same CPU, same native frontier, actual guest queue and scheduler
    // configuration. No register mutation or synthetic transfer start.
    template<class C>static bool handoff_second_transfer(C& c,const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,uint32_t site=0){
        const uint32_t pc=site?site:c.pc;
        if(!active_||v958::next_device.stage()||!v958::frontier_enabled()||!v958::time_seen||!v958::post_seen||
           !v958::frame||!v958::frame->saved_integer(c,v958::context).ok()||
           pc!=v958::transfer_call||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
           c.mmu.read32(pc)!=v958::transfer_branch||
           !v958::ack.owns_postack(active_->controller_,cause,mask,c.inst_count))return false;
        const auto a=inspect_si_transfer_arguments(c,v958::transfer_data,v958::transfer_slots,v958::transfer_callback);
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
        SiQueueHistoryResult history;
        if(v958::six_arguments_enabled())history=v958::queue_history.finish(c,a);
        const auto* evidence=v958::six_arguments_enabled()?&history:nullptr;
        if(!v958::third_ready||v958::third_ready_tick!=c.inst_count||a.packet!=v958::third_packet||
           !v958::third_admission||si_transfer_admission(a,evidence)!=v958::third_admission||
           !v958::calls.stop_before_direct(c,pc,v958::transfer_branch)||!v958::third_route.start(c,pc,v958::transfer_branch,a,v958::third_spans,v958::third_edges,v958::msr_sites,v958::transfer_data,evidence))return false;
#else
        if(!a.admitted()||!v958::calls.stop_before_direct(c,pc,v958::transfer_branch))return false;
#endif
        const auto cfg=SiTickBinding::configuration(active_->controller_,a.channel,c.inst_count);
        return cfg&&v958::ack.handoff_follow_on(v958::next_device,active_->controller_,cause,mask,c.inst_count,a.channel,a.idle,cfg->response,cfg->latency);
    }
#endif''')
    a='            if(si_completion_ack_trace.phase()!=SiCompletionAckTrace::Phase::Idle){'
    s=replace_exact(s,a,'            if(v958::active())v958::reject(8);\n'+a)
    a='        if(si_transfer_device.stage()){\n            uint32_t value=0;'
    s=replace_exact(s,a,'''#ifdef UNDERCOVER_V1025_PRIVATE_TRANSFER
        if(v958::next_device.stage()){
            uint32_t value=0;
            if(v958::ack.stage()!=5u||!v958::next_device.read(active_->controller_,off,value))v958::reject(17);
            return value;
        }
#endif
        if(v958::active()){
            uint32_t value=0;
            if(!v958::ack.read(active_->controller_,off,value))v958::reject(5);
            return value;
        }
'''+a)
    a='            if(si_transfer_device.stage()){\n                if(!si_transfer_device.write'
    return replace_exact(s,a,'''#ifdef UNDERCOVER_V1025_PRIVATE_TRANSFER
            if(v958::next_device.stage()){
                if(v958::ack.stage()!=5u||!v958::next_device.write(active_->controller_,*off,value))v958::reject(17);
            }else
#endif
            if(v958::active()){
                if(!v958::ack.write(active_->controller_,*off,value))v958::reject(6);
            }else if(si_transfer_device.stage()){
                if(!si_transfer_device.write''')

def patch_binding(s):
    a='#include "wii_second_si_dispatch_v944.h"'
    s=replace_exact(s,a,a+'\n#include "wii_second_ack_live_v958.h"\n#include "wii_si_binding_v512.h"')
    a='''            <<dispatch_visits<<" device_held=1 handler_instruction_executed=0 boot_verified=0"<<std::endl;
        std::_Exit(0);'''
    s=replace_exact(s,a,a.replace('std::_Exit(0);','''if(!v958::enabled())std::_Exit(0);
        if(!v958::start(c,reentry.captured())||
           !SiBinding::handoff_second_ack(nwii::runtime::hw::pi_intsr,nwii::runtime::hw::pi_intmr,c.inst_count))v958::reject(7);
        std::cout<<"V958_ACK_BEGIN original_handler=1 exclusive_device=1"<<std::endl;'''))
    a='template<class C>bool poll(C& c){'
    s=replace_exact(s,a,a+'\n    if(v958::active())return v958::poll(c);')
    a='template<class C>void observe(uint32_t pc,C& c){'
    return replace_exact(s,a,a+'\n    if(v958::active()){v958::observe(pc,c);return;}')

def render(roots,extra):
    h='#pragma once\n#include "wii_bounded_ack_call_route_v956.h"\nnamespace undercover::wii::v958 {\n'
    ordered=[HANDLER,*[dst for _,dst,_,_,_ in extra]]
    h+='inline constexpr uint32_t context=0x806f5318u;\n'
    h+='inline constexpr std::array<AckCallSpan,4> spans{{'+','.join(f'{{0x{a:08x}u,0x{a+4*len(roots[a]):08x}u}}' for a in ordered)+'}};\n'
    h+='inline constexpr std::array<AckCallEdge,3> edges{{'+','.join(f'{{0x{site:08x}u,0x{dst:08x}u}}' for site,dst,_,_,_ in extra)+'}};\n}\n'
    return h

def install(dol,elf,root,host):
    roots,_,indirect,_,_,_,guard,extra=plan(dol,elf)
    ordered=[HANDLER,*[dst for _,dst,_,_,_ in extra]]
    paths=sorted(root.glob('output_*.cpp'));main=root/'main_output.cpp'
    if len(paths)<20 or any(p.is_symlink() or not p.is_file() or p.stat().st_size>64*1024*1024 for p in paths+[main]):raise ValueError('second ACK tree')
    src={p:p.read_text() for p in paths};outer=main.read_text();changes={};count=0
    for a,legacy in zip(ordered,('v672','v680','v688','v693')):
        owners=[p for p,s in src.items() if owns_root(s,a)]
        if len(owners)!=1 or sum(entry_count(s,a) for s in src.values())!=1:raise ValueError('second ACK owner')
        p=owners[0];s=changes.get(p,src[p]);body=exact_function(s,a);out=body
        original=exact(dol,elf,a,len(roots[a]))
        expected={pc:(a,original[(pc-a)//4]) for pc in reachable(a,roots[a],guard,indirect)}
        # The compiler save suffix can have authenticated overlapping aliases.
        audit_native([body] if legacy=='v680' else src.values(),outer,expected)
        for site,dst,_,_,_ in extra:
            if a<=site<a+4*len(original):verify_direct(body,site,dst)
        for pc,(_,w) in expected.items():out=patch_label(out,pc,w,legacy,pc in guard)
        s=replace_exact(s,body,out);inc='#include "undercover/wii_second_ack_live_v958.h"'
        if inc not in s:s=replace_exact(s,'#include "runtime/cpu_context.h"','#include "runtime/cpu_context.h"\n'+inc)
        changes[p]=s;count+=len(expected)
    dest=root/'nWiiRuntime/include/undercover'
    files={dest/n:(host/n).read_text() for n in ('wii_second_completion_ack_v950.h','wii_bounded_ack_call_route_v956.h','wii_second_ack_live_v958.h')}
    files[dest/'v958_private_second_ack.h']=render(roots,extra)
    si=dest/'wii_si_binding_v512.h';binding=dest/'wii_live_irq_return_binding_v922.h'
    if dest.is_symlink() or any(p.exists() or p.is_symlink() for p in files) or any(p.is_symlink() or not p.is_file() for p in (si,binding)):raise ValueError('second ACK destination')
    files[si]=patch_si(si.read_text());files[binding]=patch_binding(binding.read_text())
    for p,s in {**changes,**files}.items():p.write_text(s)
    print(f'V958_ACK_ROUTE installed=1 native_labels={count} original_edges=3 exclusive_device=1 execution=0')

def main():
    p=argparse.ArgumentParser();p.add_argument('dol',type=Path);p.add_argument('elf',type=Path);p.add_argument('generated',type=Path);a=p.parse_args()
    try:
        if a.dol.stat().st_size>MAX_DOL or a.elf.stat().st_size>64*1024*1024:raise ValueError('size')
        install(a.dol.read_bytes(),a.elf.read_bytes(),a.generated,Path(__file__).parent)
    except (OSError,ValueError,UnicodeError,struct.error,IndexError,KeyError) as e:
        allowed=('second ACK label','second ACK hook','second ACK tick','second ACK tree','second ACK owner','second ACK destination','source seam','native IPC label identity','native IPC label body','native IPC coverage','native IPC dispatch','helper call label','helper direct native call','helper native return edge')
        print('V958_ACK_ROUTE installed=0 reason='+(str(e).replace(' ','_') if str(e) in allowed else 'other'));return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
