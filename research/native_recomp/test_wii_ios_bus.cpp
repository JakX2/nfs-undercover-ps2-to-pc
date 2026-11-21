#include "wii_ios_bus.h"
#include <array>
#include <cassert>
#include <iostream>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
struct Ram final:IosMemory{
    std::array<uint8_t,4096> ram{};
    bool valid(uint32_t a,uint32_t n)const override{return uint64_t(a)+n<=ram.size();}
    uint8_t read8(uint32_t a)const override{return ram.at(a);}
    void write8(uint32_t a,uint8_t v)override{ram.at(a)=v;}
};
int main(){
    Ram mem;B bus(mem);
    constexpr uint32_t req=0x100,path=0x500;
    constexpr auto en=M::IY1|M::IY2;
    auto wr=[&](uint32_t a,uint32_t v){assert(bus.write32(a,v));};
    auto rd=[&](uint32_t a){auto v=bus.read32(a);assert(v);return *v;};
    auto ack=[&](uint32_t bit){
        // A guest PPCCTRL Y1/Y2 W1C cannot clear Hollywood's separate
        // latched IPC interrupt. This ordering is exercised by the original
        // Wii SYSCONF reply path, including its second Y1 interrupt.
        assert(bit==M::Y1||bit==M::Y2);
        assert((rd(B::IPC+M::PPCCTRL)&bit)!=0u);
        assert((rd(B::IPC+H::PPC_FLAG)&H::IPC_PPC)!=0u);
        wr(B::IPC+M::PPCCTRL,en|bit);
        assert((rd(B::MIRROR+M::PPCCTRL)&bit)==0u);
        assert((rd(B::IPC+H::PPC_FLAG)&H::IPC_PPC)!=0u);
        assert((rd(B::PI_CAUSE)&H::PI_HOLLYWOOD)!=0u);
        assert(bus.external_irq_level());
        assert(bus.external_exception_pending(B::MSR_EE));
        assert(!bus.external_exception_pending(0u));
        assert(bus.tick()==S::Pump::Busy); // IRQ latch still pending
        wr(B::MIRROR+H::PPC_FLAG,H::IPC_PPC);
        assert((rd(B::IPC+H::PPC_FLAG)&H::IPC_PPC)==0u);
        assert((rd(B::PI_CAUSE)&H::PI_HOLLYWOOD)==0u);
        assert(!bus.external_irq_level());
        assert(!bus.external_exception_pending(B::MSR_EE));
    };
    unsigned n=0;for(char ch:std::string_view("/dev/stm/immediate"))mem.write8(path+n++,uint8_t(ch));
    mem.write8(path+n,0);mem.write32(req,S::Open);mem.write32(req+12,path);
    for(unsigned i=32;i<64;++i)mem.write8(req+i,0x5a);
    wr(B::IPC+M::PPCCTRL,en);wr(B::MIRROR+M::PPCMSG,req);
    assert(rd(B::IPC+M::PPCMSG)==req);
    wr(B::IPC+M::PPCCTRL,en|M::X1);
    assert(bus.tick()==S::Pump::Ack);
    assert(rd(B::MIRROR+M::PPCCTRL)&M::Y2);
    assert(rd(B::IPC+H::PPC_FLAG)==H::IPC_PPC);
    assert(rd(B::PI_CAUSE)==0&&!bus.external_irq_level());
    wr(B::IPC+H::PPC_MASK,H::IPC_PPC);
    assert(rd(B::PI_CAUSE)==H::PI_HOLLYWOOD&&!bus.external_irq_level());
    wr(B::PI_MASK,H::PI_HOLLYWOOD);
    assert(bus.external_irq_level()&&!bus.external_exception_pending(0));
    assert(bus.external_exception_pending(B::MSR_EE));
    // W1C cannot suppress an IRQ while its underlying mailbox flag persists.
    wr(B::IPC+H::PPC_FLAG,H::IPC_PPC);assert(bus.external_irq_level());
    assert(bus.tick()==S::Pump::Busy);ack(M::Y2);
    assert(bus.tick()==S::Pump::Replied);
    assert(rd(B::IPC+M::ARMMSG)==req&&rd(B::PI_CAUSE)==H::PI_HOLLYWOOD);
    assert(mem.read32(req)==S::Reply&&mem.read32(req+4)==0&&mem.read32(req+8)==S::Open);
    for(unsigned i=32;i<64;++i)assert(mem.read8(req+i)==0x5a);
    ack(M::Y1);assert(bus.tick()==S::Pump::Idle);
    assert(bus.services().is_open(0,S::Device::Immediate));
    // Exercise the complete STM startup transport, not only the first
    // open. Reuse the original request slot as a synchronous client can.
    constexpr uint32_t event=0x180,buffer=0x600;
    auto submit=[&](uint32_t slot,uint32_t command,uint32_t fd,uint32_t a=0,
                    uint32_t b=0,uint32_t c=0,uint32_t d=0,uint32_t e=0){
        const std::array<uint32_t,8> header{command,0u,fd,a,b,c,d,e};
        for(unsigned i=0;i<header.size();++i)mem.write32(slot+4u*i,header[i]);
        wr(B::IPC+M::PPCMSG,slot);
        wr(B::IPC+M::PPCCTRL,en|M::X1);
    };
    auto acknowledge=[&](S::Pump expected){
        assert(bus.tick()==expected);
        assert((rd(B::IPC+M::PPCCTRL)&(M::Y1|M::Y2))==M::Y2);
        assert(bus.external_exception_pending(B::MSR_EE));
        ack(M::Y2);
    };
    auto receive=[&](uint32_t slot,uint32_t command,uint32_t result){
        assert(bus.tick()==S::Pump::Replied);
        assert((rd(B::IPC+M::PPCCTRL)&(M::Y1|M::Y2))==M::Y1);
        assert(rd(B::IPC+M::ARMMSG)==slot);
        assert(mem.read32(slot)==S::Reply&&mem.read32(slot+4)==result);
        assert(mem.read32(slot+8)==command);
        assert(bus.external_exception_pending(B::MSR_EE));
        ack(M::Y1);
    };
    n=0;for(char ch:std::string_view("/dev/stm/eventhook"))mem.write8(path+n++,uint8_t(ch));
    mem.write8(path+n,0);
    submit(req,S::Open,0,path);
    acknowledge(S::Pump::Ack);receive(req,S::Open,1);
    assert(bus.services().is_open(0,S::Device::Immediate));
    assert(bus.services().is_open(1,S::Device::Event));
    mem.write32(buffer,0x12345678u);mem.write32(buffer+4u,0xabcdef01u);
    submit(event,S::Ioctl,1,S::EventHook,0,0,buffer,4);
    acknowledge(S::Pump::Deferred);
    assert(bus.services().event_pending()&&bus.tick()==S::Pump::Idle);
    assert(!bus.external_irq_level()&&mem.read32(event)==S::Ioctl);
    // A deferred event must not block a subsequent synchronous request.
    submit(req,S::Ioctl,0,S::GetState,0,0,buffer+8u,4);
    acknowledge(S::Pump::Ack);receive(req,S::Ioctl,0);
    assert(mem.read32(buffer+8u)==0u&&bus.services().event_pending());
    assert(mem.read32(buffer)==0x12345678u);
    assert(bus.services().signal_event(0x20000u));
    assert(!bus.external_irq_level()); // publication only on explicit tick
    receive(event,S::Ioctl,0);
    assert(mem.read32(buffer)==0x20000u&&mem.read32(buffer+4u)==0xabcdef01u);
    assert(!bus.services().event_pending()&&bus.tick()==S::Pump::Idle);
    submit(req,S::Close,1);
    acknowledge(S::Pump::Ack);receive(req,S::Close,0);
    assert(!bus.services().is_open(1,S::Device::Event));
    assert(bus.services().is_open(0,S::Device::Immediate));
    bus.set_other_pi_causes((1u<<3)|H::PI_HOLLYWOOD);
    assert(rd(B::PI_CAUSE)==(1u<<3));wr(B::PI_MASK,1u<<3);
    assert(bus.external_irq_level());bus.set_other_pi_causes(0u);assert(!bus.external_irq_level());
    for(uint32_t addr:{B::IPC+M::ARMCTRL,B::IPC+H::ARM_MASK,B::IPC+1u,B::PI_CAUSE+8u,0u,0xffffffffu}){
        assert(!bus.read32(addr)&&!bus.write32(addr,0xffffffffu));
    }
    // V183-V185 original Wii execution exposed an IOS_Open submission whose
    // live X1 bit was cleared before the next explicit scheduler boundary.
    // The native IOS intake must still process the original physical
    // pointer exactly once; clearing the flag is not a service completion.
    {
        B queued(mem);
        auto qwr=[&](uint32_t a,uint32_t v){assert(queued.write32(a,v));};
        auto qrd=[&](uint32_t a){const auto v=queued.read32(a);assert(v);return *v;};
        const std::string_view name="/dev/stm/immediate";
        for(unsigned i=0;i<name.size();++i)mem.write8(path+i,uint8_t(name[i]));
        mem.write8(path+uint32_t(name.size()),0u);
        for(unsigned i=0;i<8u;++i)mem.write32(req+4u*i,0u);
        mem.write32(req,S::Open);
        mem.write32(req+12u,path);
        qwr(B::IPC+M::PPCMSG,req);
        qwr(B::IPC+M::PPCCTRL,en|M::X1);
        qwr(B::IPC+M::PPCCTRL,en);
        assert((qrd(B::IPC+M::PPCCTRL)&M::X1)==0u);
        assert(queued.pending_native_ios_request());
        assert(mem.read32(req)==S::Open&&queued.services().queued_replies()==0u);
        // A later guest PPCMSG rewrite cannot redirect the queued request.
        qwr(B::IPC+M::PPCMSG,event);
        assert(queued.tick()==S::Pump::Ack);
        assert(!queued.pending_native_ios_request());
        assert(queued.services().is_open(0,S::Device::Immediate));
        assert(queued.services().queued_replies()==1u);
        assert((qrd(B::IPC+M::PPCCTRL)&M::Y2)!=0u);
        assert(queued.tick()==S::Pump::Busy);
        qwr(B::IPC+M::PPCCTRL,en|M::Y2);
        qwr(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        assert(queued.tick()==S::Pump::Replied);
        assert(qrd(B::IPC+M::ARMMSG)==req);
        assert(mem.read32(req)==S::Reply&&mem.read32(req+4u)==0u);
        assert(mem.read32(req+8u)==S::Open);
        qwr(B::IPC+M::PPCCTRL,en|M::Y1);
        qwr(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        assert(queued.tick()==S::Pump::Idle);
        assert(queued.services().queued_replies()==0u);
        queued.reset();
        assert(queued.tick()==S::Pump::Idle);
    }
    bus.reset();assert(rd(B::PI_MASK)==0u&&!bus.services().is_open(0,S::Device::Immediate));
    std::cout<<"PASS: integrated native IOS MMIO bus, physical 64-byte requests, successive STM opens, deferred events, ACK/reply IRQ14 and MSR.EE gating\n";
}
