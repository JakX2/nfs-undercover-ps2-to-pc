#include "wii_native_ios_transport.h"
#include <array>
#include <iostream>
#include <stdexcept>
#include <string_view>
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
int main(){
    std::array<uint8_t,8192> one{},two{};
    constexpr uint32_t other=1u<<8, en=M::IY1|M::IY2, request=0x100u,path=0x400u;
    std::atomic<uint32_t> cause{other},mask{H::PI_HOLLYWOOD};
    NativeIosTransport host(one,two,cause,mask);
    auto& ram=host.physical_ram();
    const auto put=[&](uint32_t a,uint32_t v){need(host.write32(a,v),"native register refused");};
    const auto get=[&](uint32_t a){auto v=host.read32(a);need(v.has_value(),"native read refused");return *v;};
    const auto clear=[&](uint32_t bit){
        put(0xcd000004u,en|bit);
        need((cause.load()&H::PI_HOLLYWOOD)!=0u,"PPC W1C removed distinct Hollywood latch");
        put(0xcd800030u,H::IPC_PPC);
        need(cause.load()==other,"native W1C changed unrelated PI device");
    };
    need(host.owns_byte(0xcd800031u)&&host.owns_byte(B::IPC+M::PPCMSG)&&!host.owns_byte(0x4d000000u),"alias ownership");
    need(!host.write32(0xcd000001u,0)&&!host.read32(0xcd000002u)&&!host.read32(B::PI_CAUSE)&&!host.write32(0xcd00000cu,0),"partial or unrelated access accepted");
    put(0xcd800034u,H::IPC_PPC);
    const std::string_view name="/dev/stm/immediate";
    for(std::size_t i=0;i<name.size();++i)ram.write8(path+uint32_t(i),uint8_t(name[i]));
    ram.write8(path+uint32_t(name.size()),0u);
    ram.write32(request,S::Open);ram.write32(request+12u,path);
    put(0xcd000000u,request);put(B::MIRROR+M::PPCCTRL,en|M::X1);
    need(get(B::IPC+M::PPCMSG)==request&&host.serviced_steps()==0&&ram.read32(request)==S::Open&&cause.load()==other,"MMIO serviced synchronously");
    mask.store(other|H::PI_HOLLYWOOD);
    const auto blocked=host.service_at_guest_boundary(B::MSR_EE);
    need(blocked&&blocked->progress==S::Pump::Busy&&host.serviced_steps()==0u,"unhandled PI source allowed IOS step");
    mask.store(H::PI_HOLLYWOOD);
    auto ack=host.service_at_guest_boundary(0u);
    need(ack&&ack->progress==S::Pump::Ack&&!ack->guest_exception_ready&&ram.read32(request)==S::Open&&cause.load()==(other|H::PI_HOLLYWOOD),"native ACK/PI failed");
    cause.fetch_and(~H::PI_HOLLYWOOD);
    need(host.exception_pending(B::MSR_EE)&&!host.exception_pending(0)&&cause.load()==(other|H::PI_HOLLYWOOD),"EE gate or PI W1C reassertion failed");
    mask.store(0);need(!host.exception_pending(B::MSR_EE),"live PI mask ignored");mask.store(H::PI_HOLLYWOOD);
    clear(M::Y2);
    auto reply=host.service_at_guest_boundary(B::MSR_EE);
    need(reply&&reply->progress==S::Pump::Replied&&reply->guest_exception_ready&&ram.read32(request)==S::Reply&&ram.read32(request+4u)==0u&&get(0xcd800008u)==request,"native reply failed");
    clear(M::Y1);
    need(host.serviced_steps()==2u&&!host.service_at_guest_boundary(B::MSR_EE),"unsolicited IOS tick");
    constexpr uint32_t req2=WiiPhysicalRam::MEM2_BASE+0x100u;
    const std::string_view missing="/not-mounted";
    for(std::size_t i=0;i<missing.size();++i)ram.write8(path+uint32_t(i),uint8_t(missing[i]));
    ram.write8(path+uint32_t(missing.size()),0u);
    ram.write32(req2,S::Open);ram.write32(req2+12u,path);
    put(B::IPC+M::PPCMSG,req2);put(B::IPC+M::PPCCTRL,en|M::X1);
    auto ack2=host.service_at_guest_boundary(B::MSR_EE);
    need(ack2&&ack2->progress==S::Pump::Ack,"MEM2 request ACK failed");clear(M::Y2);
    auto reply2=host.service_at_guest_boundary(B::MSR_EE);
    need(reply2&&reply2->progress==S::Pump::Replied&&ram.read32(req2)==S::Reply&&ram.read32(req2+4u)==uint32_t(S::NotFound),"negative MEM2 reply lost");clear(M::Y1);
    put(B::IPC+M::PPCMSG,0x80000100u);put(B::IPC+M::PPCCTRL,en|M::X1);
    auto bad=host.service_at_guest_boundary(B::MSR_EE);
    need(bad&&bad->progress==S::Pump::InvalidAddress&&cause.load()==other&&ram.read32(request)==S::Reply,"virtual IOS pointer was accepted");
    put(B::IPC+M::PPCCTRL,en);
    std::cout<<"PASS: native IOS transport aliases, deferred ACK/reply and PI bit ownership\n";
}
