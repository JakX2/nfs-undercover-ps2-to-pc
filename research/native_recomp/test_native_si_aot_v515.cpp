// Original-free translated PPC loop drives SI type completion at genuine native labels.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_si_binding_v512.h"
#include "undercover/wii_si_type_scheduler_v514.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI AOT boundary");}
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
    IrqBankBinding mmio(banks,&exi);
    SiController si(nw::hw::pi_intsr);SiBinding binding(si);
    using Port=SiTypeScheduler::Port;
    SiTypeScheduler scheduler(si,{Port::present({0x12,0x34,0x56}),Port::absent(),Port::absent(),Port::absent()},8);
    constexpr uint32_t ctl=0xcd006434u,buf=0xcd006480u,status=0xcd006438u,pi=0xcc003000u,back=0x80006000u;
    auto loop=[&]{
        const auto old=c.inst_count;c.pc=0x80004000;c.lr=back;c.gpr[4]=0;c.ctr=0;
        func_80004000(c);need(c.pc==back&&c.gpr[4]==3&&c.inst_count==old+10);
    };
    c.mmu.write32(buf,0x00abcdef);c.mmu.write32(ctl,0xc0010301u);
    const auto q=*si.pending();
    loop();need(si.pending()->token==q.token&&scheduler.completed()==0);
    {
        SiTickBinding tick(scheduler);
        for(unsigned i=0;i<100;++i)need(c.mmu.read32(ctl)&1u);
        loop();need(!si.pending()&&scheduler.completed()==1&&c.mmu.read32(buf)==0x123456efu);
        need((c.mmu.read32(pi)&SiController::PI_SI)&&(c.mmu.read32(ctl)&SiController::TC_INT));
        c.mmu.write32(ctl,0x80000000u);need(!(c.mmu.read32(pi)&SiController::PI_SI));
        c.mmu.write32(buf,0x00abcdefu);c.mmu.write32(ctl,0xc0010303u);
        loop();need(!si.pending()&&scheduler.completed()==2&&c.mmu.read32(buf)==0x00abcdefu);
        need(c.mmu.read32(status)==0x00080000u&&(c.mmu.read32(ctl)&SiController::COM_ERR));
        c.mmu.write32(status,0x00080000u);c.mmu.write32(ctl,0x80000000u);
        need(!c.mmu.read32(status)&&!(c.mmu.read32(pi)&SiController::PI_SI));
    }
    c.mmu.write32(buf,0);c.mmu.write32(ctl,0xc0010305u);loop();
    need(!SiTickBinding::active()&&si.pending()&&scheduler.completed()==2&&ios.serviced_steps()==0);
    std::cout<<"PASS: translated PPC instruction labels complete SI type transactions with explicit presence and absence; no interpreter or polling completion\n";
}
