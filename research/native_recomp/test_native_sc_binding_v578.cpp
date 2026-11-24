#include "runtime/cpu_context.h"
#include "wii_boot_sc_binding_v574.h"
#include "functions.h"
#include <iostream>
#include <memory>
#include <source_location>
#include <string_view>
namespace nw=nwii::runtime;
namespace sc=undercover::wii::v574;
using Route=undercover::wii::BootScRoute;
constexpr uint32_t Entry=0x805222c0,Staging=0x81000000;
static unsigned vectors=0;
static bool suppress_arm=false;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V578 binding line "+std::to_string(loc.line()));
}
namespace nwii::runtime {
extern unsigned v578_delegated;
const void* v578_route_identity();
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(pc==Route::Call){if(!suppress_arm)sc::arm(pc,c);return;}
    if(sc::vector_trace(pc,c)){++vectors;return;}
    need(pc==Entry);
}
bool process_pending_callbacks(CPUContext&){return false;}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected MMIO");}
uint32_t HW_Reg_Read32(uint32_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected MMIO");}
void HW_Reg_Write32(uint32_t,uint32_t){throw std::runtime_error("unexpected MMIO");}
}
int main(int argc,char** argv){
    need(argc==2);const std::string_view mode=argv[1];
    auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
    need(nw::v578_route_identity()==&sc::route);
    c.pc=0x80004000u;c.lr=0x80004004u;
    need(!nw::handle_syscall(c)&&nw::v578_delegated==1&&sc::route.phase()==Route::Phase::Idle);
    if(mode=="disabled"){
        c.pc=Route::Call;c.lr=Route::Caller;
        need(!sc::enabled()&&!nw::handle_syscall(c)&&nw::v578_delegated==2&&vectors==0&&sc::route.phase()==Route::Phase::Idle);
        std::cout<<"V578_SC_BINDING disabled=1 delegated=2 shared=1 fallback=0\n";return 0;
    }
    need(sc::enabled());
    for(unsigned i=0;i<sc::expected_vector.size();++i){
        c.mmu.write8(Route::Vector+i,sc::expected_vector[i]);c.mmu.write8(Route::Source+i,sc::expected_vector[i]);
    }
    c.mmu.write32(Route::Call,0x44000002u);c.mmu.write32(Route::Resume,0x4e800020u);
    for(unsigned i=0;i<32;++i)c.gpr[i]=0x12300u+i;
    c.gpr[3]=Staging;c.gpr[4]=128;c.gpr[1]=0x81701000u;
    c.pc=Entry;c.lr=Route::Caller;c.ctr=0x1234;c.msr=0x2002;c.hid0=0x110100u;
    c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;
    c.mmu.write8(Staging-1,0xa5);c.mmu.write8(Staging+128,0x5a);
    for(unsigned i=0;i<128;++i)c.mmu.write8(Staging+i,uint8_t(i*17+9));
    if(mode=="installed")c.mmu.write8(Route::Vector,sc::expected_vector[0]^1u);
    else if(mode=="source")c.mmu.write8(Route::Source,sc::expected_vector[0]^1u);
    else if(mode=="unarmed")suppress_arm=true;
    else if(mode=="irq")c.msr|=0x8000u;
    else if(mode=="caller")c.lr+=4;
    else if(mode=="return")c.mmu.write32(Route::Resume,0);
    else need(mode=="normal"||mode=="repeat");
    func_805222C0(c);
    if(mode=="repeat"){
        c.pc=Route::Call;
        nw::handle_syscall(c);need(false);
    }
    need(mode=="normal"&&vectors==1&&nw::v578_delegated==1&&sc::route.returned(c)&&c.pc==Route::Caller&&c.srr0==Route::Resume&&c.guest_flush_count==4);
    need(c.hid0==0x110100u&&c.msr==0x2002&&c.gpr[9]==c.hid0&&c.gpr[10]==(c.hid0|8u));
    for(unsigned i=0;i<4;++i)need(c.guest_flush_lines[i]==Staging+32*i);
    for(unsigned i=0;i<128;++i)need(c.mmu.read8(Staging+i)==uint8_t(i*17+9));
    need(c.mmu.read8(Staging-1)==0xa5&&c.mmu.read8(Staging+128)==0x5a);
    std::cout<<"V578_SC_BINDING native=1 shared=1 delegated=1 lines=4 fallback=0 boot_verified=0\n";
}
