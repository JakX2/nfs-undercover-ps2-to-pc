// Original-free integration against the real pinned NWii MMIO wrappers.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_irq_bootstrap_v475.h"
#include <iostream>
#include <stdexcept>
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
namespace nw=nwii::runtime;
static void need(bool ok){if(!ok)throw std::runtime_error("pinned IRQ bootstrap integration");}
int main(){
    nw::CPUContext c;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    constexpr uint32_t pi=0xcc003004u,mask=0xcd000034u,mirror=0xcd800034u;
    nw::hw::pi_intsr.store(1u<<8);
    // Inactive wrapper retains the previous runtime behavior.
    c.mmu.write32(mask,0x40000000u);need(c.mmu.read32(mask)==0);
    {
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
        NativeIosBinding binding(host);
        need(irq_boot_trace.begin(NativeIosBinding::active()));
        c.mmu.write32(pi,0xf0u);
        c.mmu.write32(mask,0x40000000u);
        need(irq_boot_trace.complete()&&irq_boot_trace.count()==2);
        need(c.mmu.read32(pi)==0xf0u&&nw::hw::pi_intmr.load()==0xf0u);
        need(c.mmu.read32(mask)==0x40000000u&&c.mmu.read32(mirror)==0x40000000u);
        need(c.mmu.read32(0x0d000034u)==0x40000000u&&c.mmu.read32(0x0d800034u)==0x40000000u);
        need(host.serviced_steps()==0&&nw::hw::legacy_calls==0&&nw::g_ipc_interrupt_delay==0);
        need(nw::hw::pi_intsr.load()==(1u<<8));
        bool rejected=false;
        try{c.mmu.write16(mask,0);}catch(const std::runtime_error&){rejected=true;}
        need(rejected&&c.mmu.read32(mask)==0x40000000u);
        // Wrong order, wrong width, and duplicate writes use real wrappers.
        for(unsigned fault=0;fault<3;++fault){
            irq_boot_trace={};need(irq_boot_trace.begin(true));
            if(fault==0)c.mmu.write32(mask,0x40000000u);
            if(fault==1)c.mmu.write16(pi,0xf0u);
            c.mmu.write32(pi,0xf0u);c.mmu.write32(mask,0x40000000u);
            if(fault==2)c.mmu.write32(mask,0x40000000u);
            need(!irq_boot_trace.complete());
        }
        need(host.serviced_steps()==0&&nw::hw::legacy_calls==0);
    }
    need(!NativeIosBinding::active()&&c.mmu.read32(mask)==0);
    nw::g_ctx_ptr=nullptr;nw::g_mmu=nullptr;
    std::cout<<"PASS: pinned native IRQ MMIO wrappers preserve PI and Hollywood masks, aliases and write ordering\n";
}
