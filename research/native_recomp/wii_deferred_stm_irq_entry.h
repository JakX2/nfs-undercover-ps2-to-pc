#pragma once
#include "wii_stm_deferred_event_gate.h"
#include "wii_external_return_v706.h"
#include "wii_scheduler_irq_entry_v1259.h"
namespace undercover::wii {
// Native external IRQ entry for the third startup transaction. Unlike
// the Open IRQ, the original caller is active, not asleep, and IOS
// has acknowledged but must not publish the deferred event reply.
template<class C,size_t N>
bool enter_deferred_stm_irq(C& c,NativeIosTransport& host,StmDeferredEventGate& gate,
                           ExternalReturnWitness& frame,const std::array<uint8_t,N>& installed,
                           uint32_t request,uint32_t active_context,uint32_t resume,uint32_t resume_word,
                           bool authenticated){
    using H=HollywoodIrq;using M=IpcMailbox;using S=StmIos;
    static_assert(N>=4&&N<=256&&N%4==0);
    const auto before=host.cold_ipc_snapshot();const auto bound=NativeIosBinding::cold_snapshot();
    auto& ram=host.physical_ram();
    auto word=[&](uint32_t a,uint32_t v){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&
               c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==v;
    };
    if(!authenticated||!bound||!same_scheduler_ipc_snapshot(before,*bound)||!gate.deferred_held(true)||
       frame.stage()||frame.failure()||!c.is_running||c.in_callback||c.dispatch_saved_ctx||
       c.pc!=resume||!word(resume,resume_word)||!(c.msr&IosBus::MSR_EE)||
       (c.msr&ExternalUnsupportedMsr)||!host.exception_pending(c.msr)||
       before.steps!=5u||before.queued||before.replies||!before.event||
       (before.control&(M::X1|M::Y1|M::Y2))!=M::Y2||!(before.control&M::IY2)||
       !(before.flags&H::IPC_PPC)||before.irq_mask!=H::IPC_PPC||
       (before.pi_cause&before.pi_mask)!=H::PI_HOLLYWOOD||
       before.ppc!=request||!request||(request&31u)||!ram.valid(request,64u)||
       ram.read32(request)!=S::Ioctl||ram.read32(request+12u)!=S::EventHook||
       (active_context&7u)||active_context<0x80000000u||uint64_t(active_context)+744u>0x81800000ull||
       !word(0x800000c0u,active_context&0x3fffffffu)||!word(0x800000d4u,active_context)||
       !word(0x800000e4u,active_context)||!c.mmu.get_ptr(active_context+712u)||
       !c.mmu.get_ptr(active_context+713u)||c.mmu.read16(active_context+712u)!=2u)return false;
    for(unsigned i=0;i<installed.size();++i)
        if(c.mmu.read8(ExternalVector+i)!=installed[i])return false;
    const auto pc=c.pc,msr=c.msr,lr=c.lr,ctr=c.ctr,xer=c.xer;
    const auto gp=c.gpr;const auto gqr=c.gqr;const auto cr=c.cr;const auto tick=c.inst_count;
    ExternalReturnWitness captured;
    if(!captured.capture(c,before.pi_cause,before.pi_mask,H::PI_HOLLYWOOD))return false;
    struct Pending{NativeIosTransport& host;bool external_exception_pending(uint32_t m)const{return host.exception_pending(m);}};
    try{
        if(enter_external_irq(c,Pending{host},installed,true)!=ExternalEntry::Entered)return false;
    }catch(const std::exception&){return false;}
    if(c.pc!=ExternalVector||c.srr0!=pc||c.srr1!=(msr&ExternalSrr1Mask)||c.msr!=(msr&~ExternalMsrClear)||
       c.gpr!=gp||c.gqr!=gqr||c.lr!=lr||c.ctr!=ctr||c.xer!=xer||c.inst_count!=tick||
       host.exception_pending(c.msr)||!same_scheduler_ipc_snapshot(before,host.cold_ipc_snapshot())||
       !gate.deferred_held(true)||!captured.pending_source(c,before.pi_cause,before.pi_mask))return false;
    for(unsigned i=0;i<8;++i)if(c.cr[i].lt!=cr[i].lt||c.cr[i].gt!=cr[i].gt||c.cr[i].eq!=cr[i].eq||c.cr[i].so!=cr[i].so)return false;
    frame=captured;return true;
}
}
