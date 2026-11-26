#include "wii_scheduler_reply_irq_v1268.h"
#include <array>
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Alias{
    WiiPhysicalRam& ram;std::span<uint8_t> mem;
    uint8_t read8(uint32_t a)const{return ram.read8(a&0x3fffffffu);}
    uint32_t read32(uint32_t a)const{return ram.read32(a&0x3fffffffu);}
    uint8_t* get_ptr(uint32_t a){const auto p=a&0x3fffffffu;return p<mem.size()?mem.data()+p:nullptr;}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Alias mmu;uint32_t pc=0x80001234u,msr=0x8032u,lr=0x80001000u,ctr=17,xer=0x80000000u;
    uint32_t srr0=0,srr1=0,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;uint64_t inst_count=123;
    std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
};
static void trial(unsigned n,unsigned first){
    std::array<uint8_t,8192> one{},two{};
    constexpr uint32_t other=1u<<8,req=0x100u,path=0x800u,en=M::IY1|M::IY2,rfi=0x80001800u;
    std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);auto& ram=host.physical_ram();
    Cpu c{{ram,one}};for(unsigned i=0;i<32;++i)c.gpr[i]=i*31u+5u;
    c.gqr[2]=0x00040004u;c.cr[1].eq=true;
    constexpr std::array<uint8_t,8> bytes{0x60,0,0,0,0x4c,0,0,0x64};
    for(unsigned i=0;i<bytes.size();++i)ram.write8(0x500+i,bytes[i]);
    ram.write32(rfi&0x3fffffffu,0x4c000064u);
    const std::string_view old=first==1u?"/dev/stm/immediate":"/dev/stm/eventhook";
    for(unsigned i=0;i<old.size();++i)ram.write8(path+i,uint8_t(old[i]));
    ram.write8(path+uint32_t(old.size()),0);ram.write32(req,S::Open);ram.write32(req+12u,path);
    assert(host.write32(B::IPC+H::PPC_MASK,H::IPC_PPC));
    assert(host.write32(B::IPC+M::PPCMSG,req)&&host.write32(B::IPC+M::PPCCTRL,en|M::X1));
    auto first_ack=host.service_at_guest_boundary(0);assert(first_ack&&first_ack->progress==S::Pump::Ack);
    assert(host.write32(B::IPC+M::PPCCTRL,en|M::Y2)&&host.write32(B::IPC+H::PPC_FLAG,H::IPC_PPC));
    auto first_reply=host.service_at_guest_boundary(0);assert(first_reply&&first_reply->progress==S::Pump::Replied&&ram.read32(req+4u)==0u);
    assert(host.write32(B::IPC+M::PPCCTRL,en|M::Y1)&&host.write32(B::IPC+H::PPC_FLAG,H::IPC_PPC));
    const std::string_view name=first==1u?"/dev/stm/eventhook":"/dev/stm/immediate";
    for(unsigned i=0;i<name.size();++i)ram.write8(path+i,uint8_t(name[i]));
    ram.write8(path+name.size(),0);ram.write32(req,S::Open);ram.write32(req+12u,path);
    assert(host.write32(B::IPC+H::PPC_MASK,H::IPC_PPC));
    assert(host.write32(B::IPC+M::PPCMSG,req));
    assert(host.write32(B::IPC+M::PPCCTRL,en|M::X1));
    const auto ack=host.service_at_guest_boundary(0);assert(ack&&ack->progress==S::Pump::Ack);
    ExternalReturnWitness prior,next;
    assert(prior.capture(c,cause.load(),mask.load(),H::PI_HOLLYWOOD));
    assert(!enter_scheduler_ipc_irq(c,host,bytes,req));
    assert(!enter_scheduler_ipc_irq(c,host,bytes,req,3u-first));
    assert(enter_scheduler_ipc_irq(c,host,bytes,req,first));
    if(n==1){assert(!enter_scheduler_reply_irq(c,host,prior,next,bytes,req,first)&&host.serviced_steps()==3u&&next.stage()==0u);return;}
    assert(host.write32(B::IPC+M::PPCCTRL,en|M::Y2));
    assert(host.write32(B::IPC+H::PPC_FLAG,H::IPC_PPC));
    auto reply=host.service_at_guest_boundary(0);
    assert(reply&&reply->progress==S::Pump::Replied&&host.serviced_steps()==4u);
    // This isolated fixture models the original loader and RFI register
    // effects. The mailbox, publication and second hardware entry are real.
    c.pc=rfi;c.inst_count+=100u;
    if(n==2){assert(!enter_scheduler_reply_irq(c,host,prior,next,bytes,req,first)&&next.stage()==0u);return;}
    assert(prior.before_pending_rfi(c,rfi,0x4c000064u,cause.load(),mask.load()));
    c.pc=c.srr0;c.msr=c.srr1;
    assert(prior.pending_rfi_return(c,cause.load(),mask.load()));
    if(n==3)c.gpr[31]^=1u;
    if(n==4)c.inst_count++;
    if(n==5)ram.write32(req+4u,0u);
    if(n==6)ram.write32(req+8u,S::Reply);
    if(n==7)mask.fetch_or(other);
    if(n==8)ram.write8(0x500u,0);
    if(n==9)c.in_callback=true;
    if(n==10)c.dispatch_saved_ctx=1;
    if(n==11)c.msr&=~B::MSR_EE;
    const auto snap=host.cold_ipc_snapshot();const auto pc=c.pc,msr=c.msr,srr0=c.srr0,srr1=c.srr1;
    const auto gp=c.gpr;const auto tick=c.inst_count;
    assert(!enter_scheduler_reply_irq(c,host,prior,next,bytes,req));
    assert(!enter_scheduler_reply_irq(c,host,prior,next,bytes,req,3u-first));
    const bool ok=enter_scheduler_reply_irq(c,host,prior,next,bytes,n==12?req+32u:req,first);
    if(n){
        assert(!ok&&next.stage()==0u&&c.pc==pc&&c.msr==msr&&c.srr0==srr0&&c.srr1==srr1&&c.gpr==gp&&c.inst_count==tick);
        assert(same_scheduler_ipc_snapshot(snap,host.cold_ipc_snapshot()));return;
    }
    assert(ok&&next.stage()==1u&&next.source()==H::PI_HOLLYWOOD&&c.pc==ExternalVector&&c.srr0==pc&&c.srr1==msr&&c.gpr==gp&&c.inst_count==tick);
    assert(!enter_scheduler_reply_irq(c,host,prior,next,bytes,req,first));
    assert(same_scheduler_ipc_snapshot(snap,host.cold_ipc_snapshot())&&host.serviced_steps()==4u);
}
int main(){
    for(unsigned first=1;first<=2;++first)for(unsigned n=0;n<=12;++n)trial(n,first);
    std::cout<<"V1367_SECOND_IRQ_CONTRACT synthetic=1 valid=2 refused=24 repeat_refused=1 native_reply=1 second_fd=1 no_service=1 original_rfi=0\n";
}
