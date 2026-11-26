#pragma once
#include "native_external_irq.h"
#include "wii_open_epoch_v1361.h"
namespace undercover::wii {
// Called only at an authenticated scheduler mtmsr continuation.
inline bool same_scheduler_ipc_snapshot(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
    return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
        a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
        a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
}
template<class C,size_t N>
bool enter_scheduler_ipc_irq(C& c,NativeIosTransport& host,
        const std::array<uint8_t,N>& installed,uint32_t request,unsigned first_kind=0){
    using M=IpcMailbox;using H=HollywoodIrq;
    const OpenTransactionEpoch epoch(first_kind);
    if(!epoch.valid()||(epoch.second()&&!epoch.acknowledged_descriptors(3u-first_kind,[&](unsigned fd,auto d){return host.services().is_open(fd,d); })))return false;
    const auto before=host.cold_ipc_snapshot();
    if(!c.is_running||c.in_callback||c.dispatch_saved_ctx||!(c.msr&IosBus::MSR_EE)||
       (before.pi_cause&before.pi_mask)!=H::PI_HOLLYWOOD||
       !(before.control&M::Y2)||(before.control&(M::Y1|M::X1))||
       !(before.control&M::IY2)||!(before.flags&H::IPC_PPC)||
       !(before.irq_mask&H::IPC_PPC)||before.steps!=epoch.ack_steps()||before.replies!=1u||
       before.queued||before.event||before.ppc!=request||(request&31u)||
       !host.physical_ram().valid(request,32u)||
       host.physical_ram().read32(request)!=StmIos::Open)return false;
    const auto pc=c.pc,msr=c.msr,lr=c.lr,ctr=c.ctr,xer=c.xer;
    const auto gp=c.gpr;const auto gqr=c.gqr;const auto ticks=c.inst_count;
    const auto pack=[](const auto& cpu){
        uint32_t v=0;
        for(const auto& f:cpu.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return v;
    };
    const auto cr=pack(c);
    struct Pending {
        NativeIosTransport& host;
        bool external_exception_pending(uint32_t msr)const{return host.exception_pending(msr);}
    };
    try{
        if(enter_external_irq(c,Pending{host},installed,true)!=ExternalEntry::Entered)return false;
    }catch(const std::exception&){return false;}
    return c.pc==ExternalVector&&c.srr0==pc&&c.srr1==(msr&ExternalSrr1Mask)&&
        c.msr==(msr&~ExternalMsrClear)&&c.gpr==gp&&c.gqr==gqr&&pack(c)==cr&&
        c.lr==lr&&c.ctr==ctr&&c.xer==xer&&c.inst_count==ticks&&
        !host.exception_pending(c.msr)&&same_scheduler_ipc_snapshot(before,host.cold_ipc_snapshot())&&
        host.physical_ram().read32(request)==StmIos::Open;
}
}
