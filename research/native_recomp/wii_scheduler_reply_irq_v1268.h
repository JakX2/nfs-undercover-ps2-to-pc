#pragma once
#include "wii_external_return_v706.h"
#include "wii_scheduler_irq_entry_v1259.h"
namespace undercover::wii {
// A second external exception is admissible only after the first original
// exception has restored the captured idle CPU via its real native RFI.
// Does not service IOS or change the saved thread/context.
template<class C,size_t N>
bool enter_scheduler_reply_irq(C& c,NativeIosTransport& host,ExternalReturnWitness& prior,
                              ExternalReturnWitness& next,const std::array<uint8_t,N>& installed,
                              uint32_t request,unsigned first_kind=0){
    using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
    const OpenTransactionEpoch epoch(first_kind);
    if(!epoch.valid()||(epoch.second()&&!epoch.acknowledged_descriptors(3u-first_kind,[&](unsigned fd,auto d){return host.services().is_open(fd,d); })))return false;
    const auto before=host.cold_ipc_snapshot();
    auto& ram=host.physical_ram();
    if(&prior==&next||next.stage()||next.failure()||prior.source()!=H::PI_HOLLYWOOD||
       !prior.pending_restored(c,before.pi_cause,before.pi_mask)||
       (before.pi_cause&before.pi_mask)!=H::PI_HOLLYWOOD||
       (before.control&(M::X1|M::Y1|M::Y2))!=M::Y1||
       !(before.control&M::IY1)||!(before.flags&H::IPC_PPC)||!(before.irq_mask&H::IPC_PPC)||
       before.steps!=epoch.reply_steps()||before.replies||before.queued||before.event||
       before.ppc!=request||before.arm!=request||!request||(request&31u)||
       !ram.valid(request,64u)||ram.read32(request)!=S::Reply||
       ram.read32(request+4u)!=epoch.result_fd()||ram.read32(request+8u)!=S::Open)return false;
    // Check the whole installed vector before recording the next capture.
    for(unsigned i=0;i<installed.size();++i)
        if(c.mmu.read8(ExternalVector+i)!=installed[i])return false;
    const auto pc=c.pc,msr=c.msr,lr=c.lr,ctr=c.ctr,xer=c.xer;
    const auto gp=c.gpr;const auto gqr=c.gqr;const auto tick=c.inst_count;
    const auto pack=[](const auto& cpu){
        uint32_t v=0;for(const auto& f:cpu.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return v;
    };
    const auto cr=pack(c);
    ExternalReturnWitness captured;
    if(!captured.capture(c,before.pi_cause,before.pi_mask,H::PI_HOLLYWOOD))return false;
    struct Pending{
        NativeIosTransport& host;
        bool external_exception_pending(uint32_t msr)const{return host.exception_pending(msr);}
    };
    try{
        if(enter_external_irq(c,Pending{host},installed,true)!=ExternalEntry::Entered)return false;
    }catch(const std::exception&){return false;}
    if(c.pc!=ExternalVector||c.srr0!=pc||c.srr1!=(msr&ExternalSrr1Mask)||
       c.msr!=(msr&~ExternalMsrClear)||c.gpr!=gp||c.gqr!=gqr||pack(c)!=cr||
       c.lr!=lr||c.ctr!=ctr||c.xer!=xer||c.inst_count!=tick||
       host.exception_pending(c.msr)||!same_scheduler_ipc_snapshot(before,host.cold_ipc_snapshot())||
       ram.read32(request)!=S::Reply||ram.read32(request+4u)!=epoch.result_fd()||ram.read32(request+8u)!=S::Open)return false;
    next=captured;
    return true;
}
}
