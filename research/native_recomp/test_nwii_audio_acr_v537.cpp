#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_si_binding_v512.h"
#include "undercover/wii_vi_clock_v522.h"
#include "undercover/wii_audio_acr_v537.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("pinned audio ACR");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){throw std::runtime_error("legacy IOS");}}
}
int main(){
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);
    unsigned legacy_reads=0,legacy_writes=0;
    d.register_region(0x0d800180u,0x0d8001d7u,[&](uint32_t){++legacy_reads;return 0x11223344u;},[&](uint32_t,uint32_t){++legacy_writes;});
    nw::hw::register_ipc(d);
    constexpr uint32_t compat=0xcd800180u,pll=0xcd8001ccu,ext=0xcd8001d0u;
    need(c.mmu.read32(compat)==0x11223344u&&legacy_reads==1);
    for(unsigned n=0;n<16;++n){
        const uint32_t a=0x12345680u^(n<<16),b=0xa955aa55u^(n<<27),e=0xf1234567u^(n<<20);
        AudioAcrBinding acr({a,b,e});ViClockBinding vi(1);
        reject([]{AudioAcrBinding duplicate({0,0,0});});
        std::atomic<uint32_t> pi{0x100};SiController si(pi);SiBinding binding(si);
        for(auto alias:{0x0d800180u,0x8d800180u,compat})need(c.mmu.read32(alias)==a);
        c.mmu.write32(compat,(a|0x100u)&~0x80u);
        c.mmu.write32(ext,c.mmu.read32(ext)&0x3fffffffu);
        c.mmu.write32(pll,(c.mmu.read32(pll)&0xf8000000u)|0x04b0ffceu);
        c.mmu.write32(ext,c.mmu.read32(ext)&~0x10000000u);
        c.mmu.write32(ext,c.mmu.read32(ext)|0x40000000u);
        c.mmu.write32(ext,c.mmu.read32(ext)|0x80000000u);
        need(c.mmu.read32(compat)==((a|0x100u)&~0x80u));
        need(c.mmu.read32(pll)==((b&0xf8000000u)|0x04b0ffceu));
        need(c.mmu.read32(ext)==((e&~0xd0000000u)|0xc0000000u));
        const auto final=c.mmu.read32(ext);
        reject([&]{c.mmu.write32(ext,final^1u);});
        reject([&]{c.mmu.read16(ext);});reject([&]{c.mmu.read8(ext);});
        reject([&]{c.mmu.read32(ext+1);});reject([&]{c.mmu.write_f32(ext,1.0f);});
        reject([&]{c.mmu.read64(ext-4);});reject([&]{c.mmu.read32(0x4d8001d0u);});
        need(c.mmu.read32(ext)==final);
        c.mmu.write32(0xcd006430u,0x000f0200u);
        need(c.mmu.read32(0xcd006430u)==0x000f0200u&&c.mmu.read16(0xcc00206cu)==1&&pi==0x100u);
        need(c.mmu.read32(compat+4)==0x11223344u);
        c.mmu.write32(compat+4,1);
    }
    need(!AudioAcrBinding::active()&&c.mmu.read32(compat)==0x11223344u&&legacy_reads==18&&legacy_writes==16);
    std::cout<<"PASS: 16 native audio ACR seed profiles, RMW field preservation, strict width and device isolation\n";
}
