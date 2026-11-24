// Original-free test of the real pinned NWiiRuntime MMU, IPC and PI wrappers.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_native_ios_binding.h"
#include <iostream>
#include <stdexcept>
#include <string_view>

namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;
MMU* g_mmu=nullptr;
int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
namespace hw {
static unsigned legacy_calls=0;
void vi_trigger_interrupt(){}
extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){++legacy_calls;return -4;}
}
}
using namespace undercover::wii;
using B=IosBus;using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;using Bind=NativeIosBinding;
namespace nw=nwii::runtime;
static void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
template<class F>static void rejects(F f){bool threw=false;try{f();}catch(const std::runtime_error&){threw=true;}need(threw,"unsupported access reached legacy route");}
int main(){
    nw::CPUContext cpu;nw::g_ctx_ptr=&cpu;nw::g_mmu=&cpu.mmu;
    auto& dispatcher=nw::MMIODispatcher::get();dispatcher.clear();
    nw::hw::register_ipc(dispatcher);nw::hw::register_pi(dispatcher);
    constexpr uint32_t legacy=0x4320u,req=0x100u,path=0x400u,en=M::IY1|M::IY2,other=1u<<8;
    constexpr uint32_t ppcmsg=0xcd000000u,ppcctrl=0xcd000004u,armmsg=0xcd000008u;
    constexpr uint32_t flag=0xcd800030u,mask=0xcd800034u,pi_mask=0xcc003004u,pi_cause=0xcc003000u;
    cpu.mmu.write32(ppcmsg,legacy);need(cpu.mmu.read32(ppcmsg)==legacy,"inactive wrapper changed legacy IPC");
    nw::hw::pi_intsr.store(other);cpu.mmu.write32(pi_mask,H::PI_HOLLYWOOD);
    NativeIosTransport host(cpu.mmu.mem1,cpu.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    {
        Bind scope(host);
        const std::string_view dev="/dev/stm/immediate";
        for(std::size_t i=0;i<dev.size();++i)cpu.mmu.write8(0x80000000u+path+uint32_t(i),uint8_t(dev[i]));
        cpu.mmu.write8(0x80000000u+path+uint32_t(dev.size()),0u);
        cpu.mmu.write32(0x80000000u+req,S::Open);cpu.mmu.write32(0x80000000u+req+12u,path);
        cpu.mmu.write32(mask,H::IPC_PPC);
        cpu.mmu.write32(ppcmsg,req);cpu.mmu.write32(B::MIRROR+M::PPCCTRL,en|M::X1);
        need(cpu.mmu.read32(ppcmsg)==req&&cpu.mmu.read32(B::IPC+M::PPCMSG)==req,"physical/virtual IPC alias mismatch");
        need(cpu.mmu.read32(0x80000000u+req)==S::Open&&host.serviced_steps()==0u&&nw::hw::legacy_calls==0u&&nw::g_ipc_interrupt_delay==0,"MMIO invoked synchronous legacy IOS");
        rejects([&]{cpu.mmu.write32(ppcmsg+1u,req);});
        rejects([&]{(void)cpu.mmu.read32(ppcctrl+1u);});
        rejects([&]{cpu.mmu.write32(ppcmsg+12u,1u);});
        rejects([&]{(void)cpu.mmu.read16(ppcctrl);});
        rejects([&]{cpu.mmu.write16(ppcctrl,1u);});
        auto ack=Bind::service_at_guest_boundary(0u);
        need(ack&&ack->progress==S::Pump::Ack&&!ack->guest_exception_ready,"native ACK did not respect EE");
        need(cpu.mmu.read32(0x80000000u+req)==S::Open&&(cpu.mmu.read32(ppcctrl)&M::Y2)!=0u,"ACK became early reply");
        need(cpu.mmu.read32(pi_cause)==(other|H::PI_HOLLYWOOD),"Hollywood cause missing");
        cpu.mmu.write32(pi_cause,H::PI_HOLLYWOOD);
        need(cpu.mmu.read32(pi_cause)==(other|H::PI_HOLLYWOOD),"legacy PI W1C suppressed live source");
        cpu.mmu.write32(ppcctrl,en|M::Y2);
        need(cpu.mmu.read32(pi_cause)==(other|H::PI_HOLLYWOOD),"mailbox W1C collapsed distinct IRQ latch");
        cpu.mmu.write32(flag,H::IPC_PPC);need(cpu.mmu.read32(pi_cause)==other,"Hollywood W1C failed");
        auto reply=Bind::service_at_guest_boundary(B::MSR_EE);
        need(reply&&reply->progress==S::Pump::Replied&&reply->guest_exception_ready,"native reply missing");
        need(cpu.mmu.read32(armmsg)==req&&cpu.mmu.read32(0x80000000u+req)==S::Reply&&cpu.mmu.read32(0x80000000u+req+4u)==0u,"reply data not shared with MMU");
        cpu.mmu.write32(ppcctrl,en|M::Y1);cpu.mmu.write32(flag,H::IPC_PPC);
        need(nw::hw::legacy_calls==0u&&nw::g_ipc_interrupt_delay==0&&cpu.mmu.read32(pi_cause)==other,"native transport leaked into legacy IPC");
    }
    need(cpu.mmu.read32(ppcmsg)==legacy&&!Bind::active(),"scope exit changed legacy state");
    nw::g_ctx_ptr=nullptr;nw::g_mmu=nullptr;
    std::cout<<"PASS: pinned NWii MMU and MMIO wrappers use opt-in asynchronous IOS transport\n";
}
