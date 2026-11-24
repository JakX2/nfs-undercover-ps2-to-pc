// Original-free guest MMIO writes and native instruction-boundary ARAM DMA.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_aram_binding_v553.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("ARAM AOT boundary");}
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){throw std::runtime_error("legacy IOS");}}
bool process_pending_callbacks(CPUContext&){return false;}
bool handle_syscall(CPUContext&){throw std::runtime_error("syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter");}
}
#ifdef V438_SPLIT
#include "functions.h"
#else
void func_80004000(nw::CPUContext&);
void func_80004100(nw::CPUContext&);
#endif
template<class F>static void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);
    WiiPhysicalRam ram(c.mmu.mem1,c.mmu.mem2);
    auto& pi=nw::hw::pi_intsr;constexpr uint32_t Other=0x108u,Ctrl=0xcc00500au,Info=0xcc005012u,Count=0xcc005028u,Back=0x80006000u;
    pi.store(Other);AramDma dma(ram,pi,8);AramBinding bind(dma);
    reject([&]{AramBinding duplicate(dma);});
    reject([&]{c.mmu.write8(Ctrl,1);});reject([&]{c.mmu.read32(Ctrl);});
    reject([&]{c.mmu.write16(Count,32);});reject([&]{c.mmu.read16(0xcc005004u);});
    reject([&]{c.mmu.read16(0x4c00500au);});
    for(unsigned trial=0;trial<16;++trial){
        const bool reverse=trial&1u;const uint32_t source=reverse?0x90000040u:0x80000100u,dest=reverse?0x80000100u:0x90000040u;
        for(unsigned i=0;i<64;++i){c.mmu.write8(source+i,uint8_t(i*13+trial));c.mmu.write8(dest+i,0xa7);}
        c.mmu.write8(dest-1,0x5c);c.mmu.write8(dest+64,0x5c);
        c.pc=0x80004000;c.lr=Back;c.gpr[8]=64|(reverse?AramDma::Reverse:0);c.gpr[9]=0x100;c.gpr[10]=0x40;
        func_80004000(c);
        need(c.pc==Back&&c.gpr[5]==0x60u&&dma.completed()==trial+1&&c.mmu.read16(Info)==0x43);
        need(c.mmu.read32(Count)==(reverse?AramDma::Reverse:0));
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(dest+i)==c.mmu.read8(source+i));
        need(c.mmu.read8(dest-1)==0x5c&&c.mmu.read8(dest+64)==0x5c);
        need(pi==(Other|AramDma::PiDsp));
        c.mmu.write32(0xcc003000u,AramDma::PiDsp);need(pi==(Other|AramDma::PiDsp));
        c.pc=0x80004100;c.lr=Back;func_80004100(c);
        need(c.pc==Back&&pi==Other&&c.mmu.read16(Ctrl)==0x40);
    }
    std::cout<<"PASS: 16 translated PPC ARAM DMA and guest W1C trials, actual MEM1/MEM2, strict MMIO and native ticks, no interpreter\n";
}
