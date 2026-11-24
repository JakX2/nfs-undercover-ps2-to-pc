// Original-free translated PPC loop drives SI type completion at genuine native labels.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_si_binding_v512.h"
#include "undercover/wii_si_type_scheduler_v514.h"
#include "undercover/wii_si_discovery_witness_v529.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI discovery AOT witness");}
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
    constexpr uint32_t ctl=0xcd006434u,buf=0xcd006480u,status=0xcd006438u,pi=0xcc003000u,back=0x80006000u;
    auto loop=[&]{
        const auto old=c.inst_count;c.pc=0x80004000;c.lr=back;c.gpr[4]=0;c.ctr=0;
        func_80004000(c);need(c.pc==back&&c.gpr[4]==3&&c.inst_count==old+10);
    };
    using Port=SiTypeScheduler::Port;
    for(unsigned fault=0;fault<=7;++fault){
        si_discovery_trace={};nw::hw::pi_intsr=0x100u;
        SiController si(nw::hw::pi_intsr);SiBinding binding(si);
        SiTypeScheduler scheduler(si,{fault==1?Port::present({1,2,3}):Port::absent(),Port::absent(),Port::absent(),Port::absent()},fault==6?100u:8u);
        need(si_discovery_trace.begin());
        need(c.mmu.read32(status)==0);
        if(fault==2)c.mmu.read32(status);
        c.mmu.write32(status,fault==3?0x000f0000u:0u);
        if(fault==4)c.mmu.read32(ctl);
        c.mmu.write32(buf,fault==5?0x00000001u:0u);
        need(c.mmu.read32(ctl)==0);
        c.mmu.write32(ctl,0xc0010301u);
        need(si.pending().has_value());
        if(fault==7){loop();need(si.pending().has_value()&&scheduler.completed()==0);}
        else{SiTickBinding tick(scheduler);loop();}
        need(si_discovery_trace.finish()==(fault==0));
        if(!fault){
            need(scheduler.completed()==1&&!si.pending()&&si_discovery_trace.tick()<=c.inst_count);
            need(c.mmu.read32(ctl)==0xe0010300u&&c.mmu.read32(status)==0x08000000u&&c.mmu.read32(buf)==0);
            need(c.mmu.read32(pi)==(0x100u|SiController::PI_SI));
            c.mmu.write32(status,0x08000000u);c.mmu.write32(ctl,SiController::TC_INT);
            need(c.mmu.read32(status)==0&&c.mmu.read32(pi)==0x100u);
        }
        if(fault==6||fault==7)need(si.pending().has_value()&&scheduler.completed()==0&&c.mmu.read32(pi)==0x100u);
    }
    need(ios.serviced_steps()==0);
    std::cout<<"PASS: actual generated PPC and MMIO drive cold SI NOREP witness; seven negative controls; no interpreter\n";
}
