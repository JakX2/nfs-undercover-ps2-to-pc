#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_si_binding_v512.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("pinned SI binding");}
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
    unsigned legacy=0;
    d.register_region(0x0d006430u,0x0d006433u,[&](uint32_t){++legacy;return 0xfeedu;},[&](uint32_t,uint32_t){++legacy;});
    nw::hw::register_ipc(d);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,nw::hw::pi_intsr,nw::hw::pi_intmr);
    NativeIosBinding native(ios);WiiIrqBanks banks(nw::hw::pi_intsr);ExiController exi(banks,&ios.physical_ram());
    IrqBankBinding exi_mmio(banks,&exi);SiController si(nw::hw::pi_intsr);
    constexpr uint32_t poll=0xcd006430u,control=poll+4,status=poll+8,buf=0xcd006480u,pi=0xcc003000u;
    need(c.mmu.read32(poll)==0xfeedu&&legacy==1);
    {
        SiBinding binding(si);
        c.mmu.write32(poll,0x000f0200u);
        for(auto a:{poll,0x0d006430u,0x8d006430u,0xcd806430u})need(c.mmu.read32(a)==0x000f0200u);
        c.mmu.write32(status,0x0f000000u);c.mmu.write32(control,0x80000000u);
        c.mmu.write32(buf,0x10203040u);c.mmu.write32(control,0xc0010301u);
        auto q=*si.pending();need(q.tx[0]==0x10&&q.in_length==3&&q.out_length==1);
        for(unsigned i=0;i<100;++i)need(c.mmu.read32(control)&1u);
        reject([&]{c.mmu.read16(control);});reject([&]{c.mmu.read8(control);});
        reject([&]{c.mmu.read64(buf);});reject([&]{c.mmu.write_f32(poll,1);});
        reject([&]{c.mmu.read32(0x4d006434u);});reject([&]{c.mmu.read32(control+1);});
        reject([&]{c.mmu.read32(0xcd006440u);});
        const std::array<uint8_t,3> response{0x12,0x34,0x56};si.complete(q.token,response);
        need(c.mmu.read32(buf)==0x12345640u&&(c.mmu.read32(pi)&SiController::PI_SI));
        nw::hw::pi_intsr.fetch_and(~SiController::PI_SI);
        need(c.mmu.read32(pi)&SiController::PI_SI);
        c.mmu.write32(control,0x80000000u);need(!(c.mmu.read32(pi)&SiController::PI_SI));
        need(c.mmu.read32(0xcd00680cu)==0&&ios.serviced_steps()==0&&legacy==1);
    }
    need(!SiBinding::active()&&c.mmu.read32(poll)==0xfeedu&&legacy==2);
    std::cout<<"PASS: pinned native SI register aliases, explicit transfer completion, strict widths and shared PI IRQ\n";
}
