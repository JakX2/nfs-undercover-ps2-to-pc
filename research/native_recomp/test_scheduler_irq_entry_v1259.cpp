#include "wii_scheduler_irq_entry_v1259.h"
#include <array>
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Alias{WiiPhysicalRam& ram;uint8_t read8(uint32_t a)const{return ram.read8(a&0x3fffffffu);}};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Alias mmu;uint32_t pc=0x80001234u,msr=0x8032u,lr=0x80001000u,ctr=17,xer=0x80000000u;
    uint32_t srr0=0,srr1=0,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;
    uint64_t inst_count=123;
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Cr,8> cr{};
};
int main(){
    std::array<uint8_t,8192> one{},two{};
    constexpr uint32_t other=1u<<8,req=0x100u,path=0x800u,en=M::IY1|M::IY2;
    std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);auto& ram=host.physical_ram();
    Cpu c{{ram}};for(unsigned i=0;i<32;++i)c.gpr[i]=i*13u+7u;
    c.gqr[3]=0x00040004u;c.cr[5].eq=true;
    constexpr std::array<uint8_t,8> bytes{0x60,0,0,0,0x4c,0,0,0x64};
    for(unsigned i=0;i<bytes.size();++i)ram.write8(0x500+i,bytes[i]);
    auto enter=[&](uint32_t p=0x100u){return enter_scheduler_ipc_irq(c,host,bytes,p);};
    auto rejected=[&]{assert(c.pc==0x80001234u&&c.srr0==0&&c.srr1==0&&c.inst_count==123u);};
    assert(!enter());rejected();
    constexpr std::string_view name="/dev/stm/immediate";
    for(unsigned i=0;i<name.size();++i)ram.write8(path+i,uint8_t(name[i]));
    ram.write8(path+name.size(),0);ram.write32(req,S::Open);ram.write32(req+12u,path);
    assert(host.write32(B::IPC+H::PPC_MASK,H::IPC_PPC));
    assert(host.write32(B::IPC+M::PPCMSG,req));
    assert(host.write32(B::IPC+M::PPCCTRL,en|M::X1));
    assert(!enter());rejected();
    const auto ack=host.service_at_guest_boundary(0);
    assert(ack&&ack->progress==S::Pump::Ack);
    const auto snapshot=host.cold_ipc_snapshot();
    assert(!enter(req+32u));rejected();
    c.msr&=~B::MSR_EE;assert(!enter());rejected();c.msr|=B::MSR_EE;
    c.dispatch_saved_ctx=1;assert(!enter());rejected();c.dispatch_saved_ctx=0;
    c.in_callback=true;assert(!enter());rejected();c.in_callback=false;
    mask=0;assert(!enter());rejected();mask=other|H::PI_HOLLYWOOD;
    assert(!enter());rejected();mask=H::PI_HOLLYWOOD;
    ram.write8(0x500,0);assert(!enter());rejected();ram.write8(0x500,bytes[0]);
    assert(same_scheduler_ipc_snapshot(snapshot,host.cold_ipc_snapshot()));
    const auto gp=c.gpr;assert(enter());
    assert(c.pc==ExternalVector&&c.srr0==0x80001234u&&c.srr1==0x8032u&&c.gpr==gp);
    assert(!enter()&&host.serviced_steps()==1u&&ram.read32(req)==S::Open);
    assert(same_scheduler_ipc_snapshot(snapshot,host.cold_ipc_snapshot()));
    std::cout<<"V1259_IRQ_ENTRY_TEST valid=1 refusals=10 no_service=1\n";
}
