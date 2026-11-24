#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_si_binding_v512.h"
#include "undercover/wii_vi_clock_v522.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("pinned VI clock");}
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
    unsigned reads=0,writes=0;
    d.register_region(0xcc00206cu,0xcc00206fu,[&](uint32_t){++reads;return 0x1234u;},[&](uint32_t,uint32_t){++writes;});
    constexpr uint32_t clk=0xcc00206cu,other=clk+2;
    need(c.mmu.read16(clk)==0x1234&&reads==1);
    reject([]{ViClockBinding invalid(2);});
    {
        ViClockBinding clock(1);
        reject([]{ViClockBinding duplicate(0);});
        for(auto addr:{clk,0x0c00206cu,0x8c00206cu})need(c.mmu.read16(addr)==1);
        need(reads==1&&ViClockBinding::selected()==1);
        c.mmu.write16(clk,0);need(c.mmu.read16(clk)==0&&ViClockBinding::selected()==0);
        c.mmu.write16(0x0c00206cu,1);need(c.mmu.read16(0x8c00206cu)==1&&writes==0);
        reject([&]{c.mmu.write16(clk,2);});reject([&]{c.mmu.read8(clk);});
        reject([&]{c.mmu.read32(clk);});reject([&]{c.mmu.write_f32(clk,1);});
        reject([&]{c.mmu.read16(clk+1);});reject([&]{c.mmu.read16(0x4c00206cu);});
        reject([&]{c.mmu.read64(clk-4);});need(c.mmu.read16(clk)==1);
        need(c.mmu.read16(other)==0x1234&&reads==2);
        c.mmu.write16(other,0x4321);need(writes==1);
        std::atomic<uint32_t> pi{0};SiController si(pi);SiBinding binding(si);
        c.mmu.write32(0xcd006430u,0x000f0200u);
        need(c.mmu.read32(0xcd006430u)==0x000f0200u&&c.mmu.read16(clk)==1&&pi==0);
    }
    need(!ViClockBinding::active()&&!ViClockBinding::selected()&&c.mmu.read16(clk)==0x1234&&reads==3);
    std::cout<<"PASS: pinned VI clock 16-bit MMIO, both selectors, strict access, adjacent and SI isolation\n";
}
