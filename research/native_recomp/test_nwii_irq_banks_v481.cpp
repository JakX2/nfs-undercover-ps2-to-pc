#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_irq_bank_binding_v481.h"
#include <iostream>
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
void vi_trigger_interrupt(){}
extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){return -4;}
}
}
using namespace undercover::wii;
namespace nw=nwii::runtime;
static void need(bool ok){if(!ok)throw std::runtime_error("pinned bank route");}
template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}need(caught);}
int main(){
    nw::CPUContext c;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    constexpr uint32_t mi=0xcc00401cu,exi=0xcd006800u,ai=0xcd006c00u,pi=0xcc003000u;
    constexpr uint32_t other=1u<<8;
    nw::hw::pi_intsr=other;
    {
        NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
        NativeIosBinding native(ios);
        WiiIrqBanks banks(nw::hw::pi_intsr);IrqBankBinding binding(banks);
        c.mmu.write16(mi,0x15);banks.raise_mi(1);
        need(c.mmu.read16(mi)==0x15&&c.mmu.read16(mi+2)==1);
        need(c.mmu.read32(pi)==(other|WiiIrqBanks::PI_MI));
        c.mmu.write32(pi,WiiIrqBanks::PI_MI);need(c.mmu.read32(pi)==(other|WiiIrqBanks::PI_MI));
        c.mmu.write16(mi+2,1);need(c.mmu.read32(pi)==other);
        banks.raise_exi(1,2);c.mmu.write32(exi+0x14,1);
        need(c.mmu.read32(exi+0x14)==3&&c.mmu.read32(exi+0x800014)==3);
        c.mmu.write32(exi+0x800014,2);need(c.mmu.read32(exi+0x14)==0);
        banks.raise_ai();c.mmu.write32(ai,4);
        need(c.mmu.read32(ai)==12&&c.mmu.read32(pi)==(other|WiiIrqBanks::PI_AI));
        c.mmu.write32(ai,8);need(c.mmu.read32(pi)==other);
        c.mmu.write32(0xcd000034u,0x40000000u);
        need(c.mmu.read32(0xcd800034u)==0x40000000u&&ios.serviced_steps()==0);
        reject([&]{c.mmu.read32(mi);});reject([&]{c.mmu.write8(mi,1);});
        reject([&]{c.mmu.write16(exi,1);});reject([&]{c.mmu.write64(exi,0);});
        reject([&]{c.mmu.write32(exi+4,0);});reject([&]{c.mmu.write32(ai+4,0);});
        reject([&]{c.mmu.write32(0x4d006800u,0);});
        reject([&]{c.mmu.write_f32(ai,0.0f);});reject([&]{c.mmu.write32(ai,1);});
        c.mmu.write32(0x80001000u,0x12345678u);need(c.mmu.read32(0x80001000u)==0x12345678u);
    }
    need(!IrqBankBinding::active()&&!NativeIosBinding::active());
    nw::g_ctx_ptr=nullptr;nw::g_mmu=nullptr;
    std::cout<<"PASS: pinned MMU routes cold MI/EXI/AI registers, aliases and widths without disturbing IOS or RAM\n";
}
