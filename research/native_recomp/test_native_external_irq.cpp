#include "native_external_irq.h"
#include "wii_ios_bus.h"
#include <array>
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Ram final:IosMemory {
    std::array<uint8_t,8192> bytes{};
    bool valid(uint32_t a,uint32_t n)const override{return uint64_t(a)+n<=bytes.size();}
    uint8_t read8(uint32_t a)const override{return bytes.at(a);}
    void write8(uint32_t a,uint8_t b)override{bytes.at(a)=b;}
};
struct Alias {
    Ram& ram;
    uint8_t read8(uint32_t a)const{return ram.read8(a&0x3fffffffu);}
};
struct Context {
    Alias mmu;
    uint32_t pc=0x80001234u,msr=0x0000b032u,srr0=0x11223344u,srr1=0x55667788u;
    uint32_t dispatch_saved_ctx=0,lr=0xaabbccddu,ctr=42;
    std::array<uint32_t,32> gpr{};
};
int main(){
    Ram ram;B bus(ram);Context c{{ram}};
    constexpr std::array<uint8_t,8> synthetic_vector{0x60,0,0,0,0x4c,0,0,0x64};
    for(unsigned i=0;i<synthetic_vector.size();++i)ram.write8(0x500+i,synthetic_vector[i]);
    for(unsigned r=0;r<32;++r)c.gpr[r]=0x90000000u+r;
    const auto gp=c.gpr;
    auto enter=[&](bool safe=true){return enter_external_irq(c,bus,synthetic_vector,safe);};
    const uint32_t oldpc=c.pc,oldmsr=c.msr,old0=c.srr0,old1=c.srr1;
    auto unchanged=[&]{assert(c.pc==oldpc&&c.msr==oldmsr&&c.srr0==old0&&c.srr1==old1&&c.gpr==gp);};
    assert(enter()==ExternalEntry::NotPending);unchanged();
    auto wr=[&](uint32_t a,uint32_t v){assert(bus.write32(a,v));};
    constexpr uint32_t req=0x100,path=0x800;
    unsigned n=0;for(char ch:std::string_view("/dev/stm/immediate"))ram.write8(path+n++,uint8_t(ch));
    ram.write8(path+n,0);ram.write32(req,S::Open);ram.write32(req+12,path);
    wr(B::IPC+H::PPC_MASK,H::IPC_PPC);wr(B::PI_MASK,H::PI_HOLLYWOOD);
    wr(B::IPC+M::PPCMSG,req);wr(B::IPC+M::PPCCTRL,M::IY1|M::IY2|M::X1);
    assert(bus.tick()==S::Pump::Ack&&bus.external_irq_level());
    c.msr&=~B::MSR_EE;assert(enter()==ExternalEntry::NotPending);c.msr=oldmsr;unchanged();
    assert(enter(false)==ExternalEntry::Deferred);unchanged();
    c.dispatch_saved_ctx=0x80001000u;assert(enter()==ExternalEntry::Deferred);c.dispatch_saved_ctx=0;unchanged();
    bool rejected=false;ram.write8(0x500,0);
    try{(void)enter();}catch(const std::runtime_error&){rejected=true;}
    assert(rejected);unchanged();ram.write8(0x500,synthetic_vector[0]);
    for(uint32_t bit:{0x10000u,0x40u,1u}){
        c.msr=oldmsr|bit;rejected=false;try{(void)enter();}catch(const std::runtime_error&){rejected=true;}
        assert(rejected&&c.pc==oldpc&&c.srr0==old0&&c.srr1==old1);c.msr=oldmsr;
    }
    assert(enter()==ExternalEntry::Entered);
    assert(c.pc==ExternalVector&&c.srr0==oldpc&&c.srr1==oldmsr&&c.msr==0x1000u);
    assert(c.gpr==gp&&c.lr==0xaabbccddu&&c.ctr==42u&&c.dispatch_saved_ctx==0);
    assert(bus.external_irq_level()&&enter()==ExternalEntry::NotPending);
    // Synthetic handler-side MMIO only: acknowledge the observed IRQ.
    // The helper itself does not clear the bus or fake a return from rfi.
    wr(B::IPC+M::PPCCTRL,M::IY1|M::IY2|M::Y2);
    assert(bus.tick()==S::Pump::Busy);
    wr(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    assert(!bus.external_irq_level()&&bus.tick()==S::Pump::Replied);
    assert(bus.external_irq_level());
    // Model the caller restoring guest execution only in this unit test.
    c.pc=c.srr0;c.msr=c.srr1;
    assert(enter()==ExternalEntry::Entered&&c.srr0==oldpc);
    wr(B::IPC+M::PPCCTRL,M::IY1|M::IY2|M::Y1);
    wr(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    assert(!bus.external_irq_level()&&bus.tick()==S::Pump::Idle);
    // Repeat the precise post-V194 boundary with a distinct guest request.
    // Broadway has already cleared visible X1, the IOS service has ACKed
    // Y2, and one completion remains deferred. The OSInit helper toggles EE
    // through the original disabled/restored states without ticking IOS.
    {
        Ram second_ram;
        B second_bus(second_ram);
        Context second{{second_ram}};
        for(unsigned i=0;i<synthetic_vector.size();++i)
            second_ram.write8(0x500+i,synthetic_vector[i]);
        constexpr uint32_t second_request=0x200u,second_path=0x900u;
        constexpr std::string_view device="/dev/stm/immediate";
        for(unsigned i=0;i<device.size();++i)
            second_ram.write8(second_path+i,uint8_t(device[i]));
        second_ram.write8(second_path+uint32_t(device.size()),0u);
        second_ram.write32(second_request,S::Open);
        second_ram.write32(second_request+12u,second_path);
        const auto second_wr=[&](uint32_t a,uint32_t v){assert(second_bus.write32(a,v));};
        second_wr(B::IPC+H::PPC_MASK,H::IPC_PPC);
        second_wr(B::PI_MASK,H::PI_HOLLYWOOD);
        second_wr(B::IPC+M::PPCMSG,second_request);
        second_wr(B::IPC+M::PPCCTRL,M::IY1|M::IY2|M::X1);
        second_wr(B::IPC+M::PPCCTRL,M::IY1|M::IY2);
        assert(second_bus.pending_native_ios_request()&&
               (second_bus.read32(B::IPC+M::PPCCTRL).value()&M::X1)==0u);
        assert(second_bus.tick()==S::Pump::Ack&&
               second_bus.services().queued_replies()==1u&&
               !second_bus.pending_native_ios_request()&&
               second_ram.read32(second_request)==S::Open);
        second.pc=0x8052f830u;
        second.lr=0x80520970u;
        second.msr=0x0000b032u;
        for(unsigned i=0;i<32u;++i)second.gpr[i]=0x90001000u+i;
        const auto original_registers=second.gpr;
        const uint32_t original_msr=second.msr;
        assert(second_bus.external_exception_pending(second.msr));
        second.msr&=~B::MSR_EE;
        assert(!second_bus.external_exception_pending(second.msr)&&
               second_bus.external_irq_level()&&
               second_bus.services().queued_replies()==1u&&
               second_ram.read32(second_request)==S::Open);
        second.msr=original_msr;
        assert(second_bus.external_exception_pending(second.msr)&&
               second_bus.services().queued_replies()==1u);
        const auto result=enter_external_irq(second,second_bus,synthetic_vector,true);
        assert(result==ExternalEntry::Entered&&
               second.pc==ExternalVector&&
               second.srr0==0x8052f830u&&
               second.srr1==(original_msr&ExternalSrr1Mask)&&
               second.msr==(original_msr&~ExternalMsrClear)&&
               second.lr==0x80520970u&&
               second.gpr==original_registers);
        assert(!second_bus.external_exception_pending(second.msr)&&
               second_bus.external_irq_level()&&
               second_bus.services().queued_replies()==1u&&
               second_ram.read32(second_request)==S::Open);
    }
    std::cout<<"PASS: native external IRQ entry at instruction boundary, SRRs, MSR, vector guard and IPC latch sequencing\n";
}
