// Original-free guest MMIO writes and native instruction-boundary ARAM DMA.
#include "runtime/cpu_context.h"
#include "runtime/hw/hw.h"
#include "undercover/wii_aram_binding_v553.h"
#include <iostream>
#include <memory>
namespace nw=nwii::runtime;using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("DSP AOT boundary");}
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
void func_80004200(nw::CPUContext&);
void func_80004300(nw::CPUContext&);
void func_80004400(nw::CPUContext&);
void func_80004500(nw::CPUContext&);
#endif
template<class F>static void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
int main(){
    using C=DspControl;using D=AramDma;
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;nw::g_ctx_ptr=&c;nw::g_mmu=&c.mmu;
    auto& d=nw::MMIODispatcher::get();d.clear();nw::hw::register_pi(d);
    WiiPhysicalRam ram(c.mmu.mem1,c.mmu.mem2);auto& pi=nw::hw::pi_intsr;
    constexpr uint32_t Other=0x108u,Ctrl=0xcc00500au,Back=0x80006000u;
    pi.store(Other);D dma(ram,pi,8);C dsp(dma);
    reject([&]{C duplicate(dma);});
    AramBinding bind(dma,dsp);
    auto call=[&](auto fn,uint32_t pc){c.pc=pc;c.lr=Back;fn(c);need(c.pc==Back);};
    auto write=[&](uint16_t value){c.gpr[4]=value;call(func_80004200,0x80004200u);return c.gpr[5];};
    auto poll=[&]{call(func_80004500,0x80004500u);return c.gpr[5];};
    reject([&]{c.mmu.write16(0xcc005004u,1);});
    reject([&]{c.mmu.write16(0xcc005006u,1);});
    reject([&]{c.mmu.read32(0xcc005000u);});
    reject([&]{c.mmu.read16(0xcc005040u);});
    reject([&]{c.mmu.read8(Ctrl);});
    for(unsigned trial=0;trial<16;++trial){
        need(write(0x8ac)==0x804&&write(0x805)==0x805);
        const auto reset=*dsp.reset_request();
        for(unsigned i=0;i<16;++i)need(poll()==0x805);
        dsp.complete_reset(reset.token);need(poll()==0x804);
        const uint32_t msg=0x12340000u|trial;
        c.gpr[4]=msg>>16;c.gpr[5]=msg&0xffff;
        call(func_80004300,0x80004300u);
        need(c.gpr[6]==0x9234&&dsp.consume_cpu_mail()==msg&&!dsp.consume_cpu_mail());
        call(func_80004400,0x80004400u);
        need(!(c.gpr[4]&0x8000u)&&!(c.gpr[6]&0x8000u));
        dsp.post_dsp_mail(0x23450000u|trial);
        call(func_80004400,0x80004400u);
        need(c.gpr[4]==0xa345u&&c.gpr[5]==trial&&c.gpr[6]==0x2345u);
        need(write(C::Halt|C::Boot|C::DspMask)==(C::Halt|C::Boot|C::DspMask));
        dsp.raise_dsp_irq();need(pi==(Other|D::PiDsp));
        // Existing generated ARAM helper sets ARAM-only mask, leaves peer
        // status pending; then re-enable the DSP mask and acknowledge ARAM.
        c.gpr[8]=64;c.gpr[9]=0x100;c.gpr[10]=0x40;
        for(unsigned i=0;i<64;++i)c.mmu.write8(0x80000100+i,uint8_t(i+trial));
        // Preserve boot mode: this helper writes 0x40, so complete the
        // explicit init transition first, avoiding a DMA during init.
        need(write(C::Halt|C::DspMask)==(C::Halt|C::DspMask|C::DspInt|C::Init));
        const auto init=*dsp.init_request();dsp.complete_init(init.token);
        call(func_80004000,0x80004000u);
        need((poll()&(D::ArInt|C::DspInt))==(D::ArInt|C::DspInt)&&dma.completed()==trial+1);
        for(unsigned i=0;i<64;++i)need(c.mmu.read8(0x90000040u+i)==uint8_t(i+trial));
        need(write(D::ArMask|C::DspMask|D::ArInt)==(D::ArMask|C::DspMask|C::DspInt));
        need(pi==(Other|D::PiDsp));
        need(write(C::DspInt)==0&&pi==Other);
    }
    std::cout<<"PASS: 16 generated PPC DSP reset/init/mailbox and mixed ARAM interrupt trials; explicit backend events, no interpreter\n";
}
