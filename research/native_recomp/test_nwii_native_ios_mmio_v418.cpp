// Original-free test of the real pinned NWiiRuntime MMU, IPC and PI wrappers.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_native_ios_binding.h"
#ifdef V422_BOUNDARY_CHECKS
#include "undercover/wii_native_ios_boundary.h"
#endif
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
#ifdef V421_WIDTH_CHECKS
        for(uint32_t a:{ppcmsg,ppcctrl,flag,mask,0x8d000000u,0x0d800030u}){
            rejects([&]{(void)cpu.mmu.read8(a);});rejects([&]{cpu.mmu.write8(a,1u);});
            rejects([&]{(void)cpu.mmu.read64(a);});rejects([&]{cpu.mmu.write64(a,0u);});
            rejects([&]{(void)cpu.mmu.read_f32(a);});rejects([&]{cpu.mmu.write_f32(a,1.0f);});
            rejects([&]{(void)cpu.mmu.read_f64(a);});rejects([&]{cpu.mmu.write_f64(a,1.0);});
        }
        rejects([&]{(void)cpu.mmu.read32(0x4d000000u);});
        rejects([&]{cpu.mmu.write32(0x4d800004u,0u);});
        rejects([&]{(void)cpu.mmu.read64(0xcd7ffffcu);});
        rejects([&]{cpu.mmu.write16(0xccffffffu,0u);});
        need(cpu.mmu.read32(ppcmsg)==req&&host.serviced_steps()==0u,"invalid access changed mailbox");
        cpu.mmu.write8(0x80000700u,0xa5u);need(cpu.mmu.read8(0x80000700u)==0xa5u,"ordinary RAM byte blocked");
        cpu.mmu.write64(0x90000000u,0x123456789abcdef0ull);need(cpu.mmu.read64(0x90000000u)==0x123456789abcdef0ull,"ordinary MEM2 access blocked");
#endif
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
#ifdef V422_BOUNDARY_CHECKS
        constexpr std::array<uint8_t,8> vector{0x60,0,0,0,0x4c,0,0,0x64};
        for(std::size_t i=0;i<vector.size();++i)cpu.mmu.write8(ExternalVector+uint32_t(i),vector[i]);
        constexpr uint32_t resume=0x80001000u,msr=0x0000b032u,req2=0x200u;
        cpu.pc=resume;cpu.msr=msr&~B::MSR_EE;cpu.gpr.fill(0x12345678u);cpu.lr=resume+4u;cpu.ctr=9u;cpu.xer=10u;
        const auto regs=cpu.gpr;
        cpu.mmu.write32(0x80000000u+req2,S::Open);cpu.mmu.write32(0x80000000u+req2+12u,path);
        cpu.mmu.write32(ppcmsg,req2);cpu.mmu.write32(ppcctrl,en|M::X1);
        auto boundary=[&](bool safe=true){return service_native_ios_boundary(host,cpu,vector,safe);};
        need(boundary(false).route==NativeBoundaryRoute::Unsafe&&host.serviced_steps()==2u,"unsafe pinned boundary pumped IOS");
        auto masked=boundary();need(masked.route==NativeBoundaryRoute::NativeMasked&&masked.service&&masked.service->progress==S::Pump::Ack&&cpu.pc==resume,"pinned boundary ACK incorrect");
        cpu.msr=msr;auto y2=boundary();
        need(y2.route==NativeBoundaryRoute::NativeEntered&&cpu.pc==ExternalVector&&cpu.srr0==resume&&cpu.srr1==(msr&ExternalSrr1Mask)&&cpu.msr==(msr&~ExternalMsrClear)&&cpu.gpr==regs&&cpu.lr==resume+4u&&cpu.ctr==9u&&cpu.xer==10u,"pinned CPU exception state incorrect");
        cpu.mmu.write32(ppcctrl,en|M::Y2);cpu.mmu.write32(flag,H::IPC_PPC);
        // Synthetic test return, not an implementation of the guest handler.
        cpu.pc=cpu.srr0;cpu.msr=msr;
        auto y1=boundary();need(y1.route==NativeBoundaryRoute::NativeEntered&&y1.service&&y1.service->progress==S::Pump::Replied&&cpu.mmu.read32(0x80000000u+req2)==S::Reply,"pinned CPU reply entry incorrect");
        cpu.mmu.write32(ppcctrl,en|M::Y1);cpu.mmu.write32(flag,H::IPC_PPC);
        cpu.pc=cpu.srr0;cpu.msr=msr;
        need(boundary().route==NativeBoundaryRoute::Idle&&host.serviced_steps()==4u&&cpu.mmu.read32(pi_cause)==other&&nw::hw::legacy_calls==0u,"pinned boundary did not preserve idle and other PI");
        std::cout<<"PASS: pinned CPU native IOS boundary with authenticated synthetic vector\n";
#endif
    }
    need(cpu.mmu.read32(ppcmsg)==legacy&&!Bind::active(),"scope exit changed legacy state");
    nw::g_ctx_ptr=nullptr;nw::g_mmu=nullptr;
    std::cout<<"PASS: pinned NWii MMU and MMIO wrappers use opt-in asynchronous IOS transport\n";
}
