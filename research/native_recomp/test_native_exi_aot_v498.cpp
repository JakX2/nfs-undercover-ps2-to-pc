// Synthetic PowerPC loop emitted by the actual pinned NWiiRecomp, not a
// manual invocation of the instruction boundary helper.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_exi_tick_binding_v497.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI AOT boundary");}
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
#endif
int main(){
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);ExiController exi(banks,&ios.physical_ram());
    IrqBankBinding mmio(banks,&exi);ExiMxDevice::Sram seed{};
    for(unsigned i=0;i<64;++i)seed[i]=uint8_t(i*13);
    ExiMxDevice mx(seed,[]{return 0x87654321u;});ExiIdEndpoint id(0xffffffffu);
    ExiEndpointScheduler sched(exi,mx,id,8);
    constexpr uint32_t csr=0xcd006800u,mar=csr+4,len=csr+8,cr=csr+12,data=csr+16,back=0x80006000;
    auto loop=[&]{
        const auto old=c.inst_count;c.pc=0x80004000;c.lr=back;c.gpr[4]=0;c.ctr=0;
        func_80004000(c);need(c.pc==back&&c.gpr[4]==3&&c.inst_count==old+10);
    };
    c.mmu.write32(csr,0x134);c.mmu.write32(data,0x20000100);c.mmu.write32(cr,0x35);
    loop();need(c.mmu.read32(cr)==0x35&&sched.completed()==0);
    {
        ExiTickBinding tick(sched);loop();need(c.mmu.read32(cr)==0x34&&sched.completed()==1);
        c.mmu.write32(mar,0x80001000);c.mmu.write32(len,64);c.mmu.write32(cr,3);
        loop();need(c.mmu.read32(cr)==2&&sched.completed()==2);
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(0x80001000+i)==seed[i]);
        c.mmu.write32(csr,8);need(!(c.mmu.read32(0xcc003000)&WiiIrqBanks::PI_EXI));
    }
    need(!ExiTickBinding::active()&&ios.serviced_steps()==0);
    std::cout<<"PASS: genuine translated PPC loop completes SRAM DMA at native instruction labels; no interpreter or polling completion\n";
}
