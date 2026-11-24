#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_si_binding_v512.h"
#include "undercover/wii_vi_clock_v522.h"
#include "undercover/wii_si_sampling_witness_v524.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("pinned SI sampling observer");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){throw std::runtime_error("legacy IOS");}}
}
int main(){
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    constexpr uint32_t clk=0xcc00206cu,poll=0xcd006430u,control=poll+4,buf=0xcd006480u;
    for(unsigned clock=0;clock<=1;++clock)for(unsigned fault=0;fault<=6;++fault){
        si_sampling_trace={};std::atomic<uint32_t> pi{0};SiController si(pi);SiBinding binding(si);
        ViClockBinding vi{uint16_t(clock)};
        // Actual MMU and hardware state, not direct calls to the observer.
        if(fault==6){c.mmu.write32(buf,0);c.mmu.write32(control,0xc0010301u);}
        need(si_sampling_trace.begin(0x000f0200u,clock));
        const uint32_t expected=(15u*(1u+clock)<<16)|0x200u;
        if(fault==1)c.mmu.write16(clk,uint16_t(clock^1u));
        if(fault==2)c.mmu.read32(control);
        const auto value=c.mmu.read16(clk);
        if(fault==3)c.mmu.read16(clk);
        c.mmu.write32(poll,expected^(fault==4?1u:0u));
        const auto status=c.mmu.read32(control);
        if(fault!=5&&fault!=6)c.mmu.write32(control,SiController::TC_INT);
        need(si_sampling_trace.finish()==(fault==0));
        if(!fault)need(value==clock&&status==0&&si.read(SiController::Poll)==expected&&pi==0);
        if(fault==6)need(si.pending()&&status==0x40010301u);
    }
    std::cout<<"PASS: actual native VI and SI MMU observer order, both clock modes and twelve negative controls\n";
}
