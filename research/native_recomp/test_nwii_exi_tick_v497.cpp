#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_exi_tick_binding_v497.h"
#include <iostream>
namespace nwii::runtime {
CPUContext* g_ctx_ptr=nullptr;MMU* g_mmu=nullptr;int g_ipc_interrupt_delay=0;
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
namespace hw {void vi_trigger_interrupt(){} extern "C" int32_t handle_ios_ipc(CPUContext&,uint32_t){return -4;}}
}
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("pinned EXI tick");}
int main(){
    nw::CPUContext c;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);nw::hw::register_ipc(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);ExiController exi(banks,&ios.physical_ram());
    IrqBankBinding mmio(banks,&exi);ExiMxDevice::Sram seed{};
    for(unsigned i=0;i<seed.size();++i)seed[i]=uint8_t(i*11);
    ExiMxDevice mx(seed,[]{return 0x12345678u;});ExiIdEndpoint id(0xffffffffu);ExiEndpointScheduler sched(exi,mx,id,8);
    constexpr uint32_t csr=0xcd006800u,mar=csr+4,len=csr+8,cr=csr+12,data=csr+16;
    c.mmu.write32(csr,0x134);c.mmu.write32(data,0x20000100u);c.mmu.write32(cr,0x35);
    for(unsigned i=0;i<20;++i){++c.inst_count;c.exi_instruction_boundary();}
    need(c.mmu.read32(cr)==0x35&&sched.completed()==0);
    {
        ExiTickBinding tick(sched);
        auto advance=[&]{++c.inst_count;c.exi_instruction_boundary();};
        advance();for(unsigned i=0;i<7;++i){advance();need(c.mmu.read32(cr)&1u);}
        advance();need(c.mmu.read32(cr)==0x34&&sched.completed()==1);
        c.mmu.write32(mar,0x80001000u);c.mmu.write32(len,64);c.mmu.write32(cr,3);
        for(unsigned i=0;i<100;++i)need(c.mmu.read32(cr)==3);
        advance();for(unsigned i=0;i<7;++i)advance();need(c.mmu.read32(cr)==3);
        advance();need(c.mmu.read32(cr)==2&&sched.completed()==2);
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(0x80001000u+i)==seed[i]);
        need((c.mmu.read32(0xcc003000u)&WiiIrqBanks::PI_EXI)!=0);
        c.mmu.write32(csr,8);need(!(c.mmu.read32(0xcc003000u)&WiiIrqBanks::PI_EXI));
        c.mmu.write32(csr,0x234);c.mmu.write32(data,0);c.mmu.write32(cr,0x15);
    }
    for(unsigned i=0;i<100;++i){++c.inst_count;c.exi_instruction_boundary();}
    need(!ExiTickBinding::active()&&c.mmu.read32(cr)==0x15&&sched.completed()==2);
    need(ios.serviced_steps()==0);
    std::cout<<"PASS: pinned native instruction boundary completes real MMIO SRAM command and DMA; polling and unbound ticks do not service\n";
}
