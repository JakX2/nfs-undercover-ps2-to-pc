// V368: authenticated-NAND-style IRQ mask writes after a genuine IOS X1 ACK.
// Original-free regression. No game executable, generated AOT or guest assets.
// Verify that the existing native IOS bus retains a real pending completion
// and IRQ cause while Broadway toggles Hollywood and PI mask registers.
#include "wii_ios_yield_scheduler.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>

using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;

static void require(bool ok,const char* what){
    if(!ok)throw std::runtime_error(what);
}
struct Ram final:IosMemory{
    std::array<uint8_t,0x2000> data{};
    bool valid(uint32_t at,uint32_t len)const override{
        return uint64_t(at)+len<=data.size();
    }
    uint8_t read8(uint32_t at)const override{return data.at(at);}
    void write8(uint32_t at,uint8_t val)override{data.at(at)=val;}
    void path(uint32_t addr,std::string_view text){
        require(valid(addr,uint32_t(text.size()+1u)),"path outside test RAM");
        for(char x:text)write8(addr++,uint8_t(x));
        write8(addr,0u);
    }
};

int main(){
    Ram ram;
    B bus(ram);
    IosYieldScheduler starlet(bus);
    constexpr uint32_t request=0x100u,path=0x400u;
    constexpr uint32_t enabled=M::IY1|M::IY2;
    const auto put=[&](uint32_t addr,uint32_t value){
        require(bus.write32(addr,value),"valid native MMIO write rejected");
    };
    const auto read=[&](uint32_t addr)->uint32_t{
        const auto value=bus.read32(addr);
        require(value.has_value(),"valid native MMIO read rejected");
        return *value;
    };
    ram.path(path,"/dev/stm/immediate");
    ram.write32(request,S::Open);
    ram.write32(request+12u,path);
    // Two independently addressable masks are first enabled.
    put(B::IPC+H::PPC_MASK,H::IPC_PPC);
    put(B::PI_MASK,H::PI_HOLLYWOOD);
    require(read(B::IPC+H::PPC_MASK)==H::IPC_PPC&&
            read(B::PI_MASK)==H::PI_HOLLYWOOD,
            "native mask readback did not preserve guest register values");
    // The genuine guest PPCMSG/X1 path, no synthetic completion.
    put(B::IPC+M::PPCMSG,request);
    put(B::IPC+M::PPCCTRL,enabled|M::X1);
    require(bus.pending_native_ios_request()&&
            ram.read32(request)==S::Open,
            "native IOS request was not accepted before host yield");
    const auto ack=starlet.service_one(0u);
    require(ack.progress==S::Pump::Ack&&
            ack.serviced_steps==1u&&
            !bus.pending_native_ios_request()&&
            bus.services().queued_replies()==1u&&
            ack.broadway_irq_level&&!ack.guest_exception_ready&&
            ram.read32(request)==S::Open,
            "genuine native IOS ACK not recorded before mask test");
    require((read(B::IPC+H::PPC_FLAG)&H::IPC_PPC)!=0u,
            "real native IOS ACK did not leave a pending Hollywood cause");

    // A post-ACK original PPC mask write must change hardware routing,
    // not drop the queued IOS completion or invent an early Y1 reply.
    put(B::PI_MASK,0u);
    require(!bus.external_irq_level()&&
            read(B::IPC+H::PPC_MASK)==H::IPC_PPC&&
            (read(B::IPC+H::PPC_FLAG)&H::IPC_PPC)!=0u&&
            bus.services().queued_replies()==1u&&
            ram.read32(request)==S::Open,
            "PI mask toggle erased the pending native IOS completion");
    const auto pi_masked=starlet.service_one(B::MSR_EE);
    require(pi_masked.progress==S::Pump::Busy&&
            pi_masked.serviced_steps==2u&&
            bus.services().queued_replies()==1u&&
            ram.read32(request)==S::Open,
            "PI mask toggle published an early IOS reply");
    // The scheduler counts attempted hardware ticks even when the
    // latched Hollywood cause correctly makes Starlet return Busy.

    put(B::PI_MASK,H::PI_HOLLYWOOD);
    require(bus.external_irq_level(),"PI mask restore did not expose IRQ");
    put(B::MIRROR+H::PPC_MASK,0u);
    require(!bus.external_irq_level()&&
            read(B::IPC+H::PPC_MASK)==0u&&
            (read(B::IPC+H::PPC_FLAG)&H::IPC_PPC)!=0u&&
            bus.services().queued_replies()==1u,
            "Hollywood PPC mask toggle corrupted latched native Y2");
    const auto ppc_masked=starlet.service_one(0u);
    require(ppc_masked.progress==S::Pump::Busy&&
            ppc_masked.serviced_steps==3u&&
            bus.services().queued_replies()==1u&&
            ram.read32(request)==S::Open,
            "masked Hollywood IRQ bypassed W1C service barrier");
    put(B::MIRROR+H::PPC_MASK,H::IPC_PPC);
    require(read(B::MIRROR+H::PPC_MASK)==H::IPC_PPC&&
            bus.external_irq_level()&&
            !bus.external_exception_pending(0u)&&
            bus.external_exception_pending(B::MSR_EE),
            "Hollywood mirror mask restore lost genuine Y2 IRQ");

    // Only the original guest's two W1C acknowledgements permit a
    // later Starlet yield to publish the actual queued response.
    put(B::IPC+M::PPCCTRL,enabled|M::Y2);
    require(bus.services().queued_replies()==1u&&
            ram.read32(request)==S::Open,
            "Y2 W1C caused early native IOS reply publication");
    put(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    require(!bus.external_irq_level(),
            "Hollywood IPC flag W1C did not clear pending IRQ");
    const auto reply=starlet.service_one(B::MSR_EE);
    require(reply.progress==S::Pump::Replied&&
            starlet.serviced_steps()==4u&&
            ram.read32(request)==S::Reply&&
            ram.read32(request+8u)==S::Open&&
            bus.services().queued_replies()==0u&&
            bus.external_irq_level(),
            "real deferred IOS completion did not survive mask toggles");
    put(B::IPC+M::PPCCTRL,enabled|M::Y1);
    put(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    require(!bus.external_irq_level()&&
            !bus.pending_native_ios_request()&&
            starlet.service_one(B::MSR_EE).progress==S::Pump::Idle,
            "native IPC reply was re-published after guest W1C");
    require(!bus.write32(B::IPC+0x28u,0u),
            "unknown IPC register should remain unsupported");
    std::cout<<"PASS: original-free post-ACK NAND IRQ mask and W1C continuity V368\n";
}
