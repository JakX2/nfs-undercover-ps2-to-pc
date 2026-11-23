// V374 original-free native IOS deferred reply test, no proprietary game data.
#include "wii_nand_ios_reply_yield.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
static void need(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);}
struct Ram final:IosMemory{
    std::array<uint8_t,8192> bytes{};
    bool valid(uint32_t a,uint32_t n)const override{
        return uint64_t(a)+n<=bytes.size();
    }
    uint8_t read8(uint32_t a)const override{return bytes.at(a);}
    void write8(uint32_t a,uint8_t v)override{bytes.at(a)=v;}
    void path(uint32_t a,std::string_view s){
        need(valid(a,uint32_t(s.size()+1u)),"bad test path");
        for(char c:s)write8(a++,uint8_t(c));
        write8(a,0);
    }
};
int main(){
    Ram ram;B bus(ram);IosYieldScheduler ios(bus);
    constexpr uint32_t request=0x100u,path=0x400u,en=M::IY1|M::IY2;
    const auto put=[&](uint32_t a,uint32_t v){need(bus.write32(a,v),"MMIO rejected");};
    const auto read=[&](uint32_t a){auto x=bus.read32(a);need(x.has_value(),"read rejected");return *x;};
    need(!service_deferred_reply_at_guest_boundary(bus,0u),"idle reply invented");
    put(B::IPC+H::PPC_MASK,H::IPC_PPC);put(B::PI_MASK,H::PI_HOLLYWOOD);
    ram.path(path,"/dev/stm/immediate");
    ram.write32(request,S::Open);ram.write32(request+12u,path);
    put(B::IPC+M::PPCMSG,request);put(B::IPC+M::PPCCTRL,en|M::X1);
    need(!service_deferred_reply_at_guest_boundary(bus,0u),"request serviced before ACK");
    need(ios.service_one(0u).progress==S::Pump::Ack,"ACK missing");
    need(bus.services().queued_replies()==1u&&ram.read32(request)==S::Open,"ACK invented reply");
    need(!service_deferred_reply_at_guest_boundary(bus,0u),"pending Y2 bypassed");
    put(B::IPC+M::PPCCTRL,en|M::Y2);
    need(!service_deferred_reply_at_guest_boundary(bus,0u),"Hollywood flag bypassed");
    put(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    need(!bus.external_irq_level()&&!(read(B::IPC+M::PPCCTRL)&M::Y2),"hardware not cleared");
    const auto reply=service_deferred_reply_at_guest_boundary(bus,0u);
    need(reply&&reply->progress==S::Pump::Replied,"queued reply did not advance");
    need(!reply->guest_exception_ready&&reply->broadway_irq_level,
         "masked EE incorrectly entered guest IRQ");
    need(ram.read32(request)==S::Reply&&ram.read32(request+4u)==0u&&
         ram.read32(request+8u)==S::Open&&bus.services().queued_replies()==0u,
         "original STM reply bytes or queue changed");
    need((read(B::IPC+M::PPCCTRL)&M::Y1)!=0u&&bus.external_irq_level(),"Y1 IRQ missing");
    need(!service_deferred_reply_at_guest_boundary(bus,B::MSR_EE),"repeated Y1 publication");
    need(bus.external_exception_pending(B::MSR_EE),"Y1 not eligible after EE enabled");
    put(B::IPC+M::PPCCTRL,en|M::Y1);put(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    need(!service_deferred_reply_at_guest_boundary(bus,B::MSR_EE),"idle second reply invented");
    // Negative results are genuine IOS errors, never changed into success.
    constexpr uint32_t notfound=0x180u,badpath=0x480u;
    ram.path(badpath,"/unmounted/does-not-exist");
    ram.write32(notfound,S::Open);ram.write32(notfound+12u,badpath);
    put(B::IPC+M::PPCMSG,notfound);put(B::IPC+M::PPCCTRL,en|M::X1);
    need(ios.service_one(0u).progress==S::Pump::Ack,"second ACK missing");
    put(B::IPC+M::PPCCTRL,en|M::Y2);put(B::IPC+H::PPC_FLAG,H::IPC_PPC);
    const auto negative=service_deferred_reply_at_guest_boundary(bus,B::MSR_EE);
    need(negative&&negative->progress==S::Pump::Replied,
         "negative native IOS completion suppressed");
    need(ram.read32(notfound)==S::Reply&&
         ram.read32(notfound+4u)==uint32_t(S::NotFound)&&
         ram.read32(notfound+8u)==S::Open,
         "native IOS negative error replaced with success");
    // Two authentic X1 requests can be ACKed before either Y1 is published.
    // The native reply scheduler must preserve the original FIFO order and
    // may publish only one Y1 at each correctly acknowledged guest yield.
    {
        Ram dualram;B dual(dualram);IosYieldScheduler dualios(dual);
        constexpr uint32_t first=0x200u,second=0x280u;
        constexpr uint32_t firstpath=0x600u,secondpath=0x700u;
        const auto write=[&](uint32_t a,uint32_t v){
            need(dual.write32(a,v),"dual-request MMIO rejected");
        };
        dualram.path(firstpath,"/dev/stm/immediate");
        dualram.path(secondpath,"/dev/stm/eventhook");
        dualram.write32(first,S::Open);dualram.write32(first+12u,firstpath);
        dualram.write32(second,S::Open);dualram.write32(second+12u,secondpath);
        write(B::IPC+H::PPC_MASK,H::IPC_PPC);
        write(B::PI_MASK,H::PI_HOLLYWOOD);
        const auto ack=[&](uint32_t address){
            write(B::IPC+M::PPCMSG,address);
            write(B::IPC+M::PPCCTRL,en|M::X1);
            need(dualios.service_one(0u).progress==S::Pump::Ack,
                 "dual-request authentic Starlet ACK missing");
            write(B::IPC+M::PPCCTRL,en|M::Y2);
            write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        };
        ack(first);
        ack(second);
        need(dual.services().queued_replies()==2u&&
             dualram.read32(first)==S::Open&&dualram.read32(second)==S::Open,
             "two ACKs completed or corrupted a queued request early");
        const auto one=service_deferred_reply_at_guest_boundary(dual,0u);
        need(one&&one->progress==S::Pump::Replied&&
             dual.services().queued_replies()==1u&&
             dualram.read32(first)==S::Reply&&
             dualram.read32(second)==S::Open&&
             dual.read32(B::IPC+M::ARMMSG).value()==first,
             "first queued completion not published in FIFO order");
        need(!service_deferred_reply_at_guest_boundary(dual,0u),
             "second completion bypassed first Y1 acknowledgement");
        write(B::IPC+M::PPCCTRL,en|M::Y1);
        write(B::IPC+H::PPC_FLAG,H::IPC_PPC);
        const auto two=service_deferred_reply_at_guest_boundary(dual,0u);
        need(two&&two->progress==S::Pump::Replied&&
             dual.services().queued_replies()==0u&&
             dualram.read32(second)==S::Reply&&
             dual.read32(B::IPC+M::ARMMSG).value()==second,
             "second queued completion not published in FIFO order");
    }
    std::cout<<"PASS: V374 authentic ACK, Y2/flag, queued Y1 and negative IOS reply\n";
}
