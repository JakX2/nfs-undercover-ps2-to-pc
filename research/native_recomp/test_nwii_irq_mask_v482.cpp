#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_irq_return_witness_v482.h"
#include <iostream>
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){return -4;}}
}
namespace nw=nwii::runtime;using namespace undercover::wii;
void need(bool b){if(!b)throw std::runtime_error("pinned seven-bank IRQ integration");}
int main(){
    nw::CPUContext c;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);nw::hw::register_dsp(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);IrqBankBinding binding(banks);
    constexpr uint32_t mi=0xcc00401cu,dsp=0xcc00500au,ai=0xcd006c00u,exi=0xcd006800u,pi=0xcc003004u;
    c.mmu.write16(mi,31);c.mmu.write16(dsp,0x950);c.mmu.write32(ai,4);
    c.mmu.write32(exi,0x405);c.mmu.write32(exi+0x14,0x405);c.mmu.write32(exi+0x28,5);
    need(irq_mask_io.begin(0));c.mmu.write16(mi,0);need(irq_mask_io.finish());
    need(irq_mask_io.begin(1));c.mmu.write16(dsp,uint16_t(c.mmu.read16(dsp)&0xfe07u));need(irq_mask_io.finish());
    constexpr std::array<uint32_t,4> regs{ai,exi,exi+0x14,exi+0x28};
    constexpr std::array<uint32_t,4> masks{0xffffffd3u,0xffffd3f0u,0xfffff3f0u,0xfffffff0u};
    for(unsigned i=0;i<4;++i){
        need(irq_mask_io.begin(i+2));c.mmu.write32(regs[i],c.mmu.read32(regs[i])&masks[i]);need(irq_mask_io.finish());
    }
    need(irq_mask_io.begin(6));c.mmu.write32(pi,0xf0);need(irq_mask_io.finish());
    need(irq_mask_io.done()==7&&c.mmu.read16(mi)==0&&(c.mmu.read16(dsp)&0x150)==0&&c.mmu.read32(pi)==0xf0);
    for(auto a:regs)need((c.mmu.read32(a)&0x405u)==0);
    irq_mask_io={};need(irq_mask_io.begin(0));c.mmu.write32(0xcd000034u,0x40000000u);
    c.mmu.write16(mi,0);need(!irq_mask_io.finish());need(ios.serviced_steps()==0);
    std::cout<<"PASS: real pinned DSP/PI and native MI/EXI/AI transaction census, unexpected IOS rejected\n";
}
