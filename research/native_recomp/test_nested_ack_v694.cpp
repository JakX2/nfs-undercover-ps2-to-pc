#include "runtime/cpu_context.h"
#include "undercover/wii_si_ack_binding_v672.h"
#include "undercover/wii_si_type_scheduler_v514.h"
#include <memory>
#include <stdexcept>
#include <string>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,A=0x80005000u,B=0x80006000u,N=0x80007000u,D=0x80008000u,Frame=0x80010000u,Other=0x100u;
static void need(bool ok){if(!ok)throw std::runtime_error("V694 AOT assertion");}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static CPUContext* active=nullptr;
static SiController* controller=nullptr;
void trace_call(uint32_t pc,CPUContext& c){
    need(&c==active&&c.pc==pc);
    if(pc==H){v672::begin(c);return;}
    v672::observe(pc,c);
}
bool process_pending_callbacks(CPUContext& c){return v672::active()?v672::poll(c):false;}
bool handle_syscall(CPUContext&){throw std::runtime_error("unexpected syscall");}
void interpret_step(CPUContext&){throw std::runtime_error("V694 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V694 micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V694 null call");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V694 unexpected MMIO16");}
uint32_t HW_Reg_Read32(uint32_t a){auto v=SiBinding::read32(a);need(v.has_value());return *v;}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V694 unexpected MMIO16");}
void HW_Reg_Write32(uint32_t a,uint32_t value){
    using namespace hw;
    need(active&&controller&&a==0x0d006434u&&value==0xe0010300u&&pi_intsr==(Other|SiController::PI_SI));
    for(unsigned r=29;r<32;++r)need(active->mmu.read32(Frame-4*(32-r))==active->gpr[r]);
    need(active->mmu.read32(Frame-16)==0xdeadbeefu);
    need(SiBinding::write32(a,value));
    need(pi_intsr==Other&&pi_intmr==SiController::PI_SI);
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
static uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
int main(int argc,char**argv){
    using namespace nwii::runtime;using namespace nwii::runtime::hw;
    need(argc==2);std::string mode=argv[1];
    pi_intsr=Other;pi_intmr=SiController::PI_SI;
    SiController ctl(pi_intsr);SiBinding bind(ctl);controller=&ctl;
    using Port=SiTypeScheduler::Port;
    SiTypeScheduler sched(ctl,{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
    need(SiBinding::write32(0xcd006434u,0xc0010301u));sched.advance(1);sched.advance(9);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;active=&c;
    auto put=[&](uint32_t a,std::initializer_list<uint32_t> w){for(auto x:w){c.mmu.write32(a,x);a+=4;}};
    put(H,{bl(H,A+4),bl(H+4,B),0x91070000u,0x60000000u,0x4e800020u});
    for(unsigned r=28;r<32;++r)c.mmu.write32(A+4*(r-28),0x900b0000u|(r<<21)|(uint32_t(-4*int(32-r))&0xffffu));
    c.mmu.write32(A+16,0x4e800020u);
    put(B,{0x7c0802a6u,0x90010004u,bl(B+8,N),0x80010004u,0x7c0803a6u,0x910c0000u,0x4e800020u});
    put(N,{0x910a0000u,0x2c090000u,0x41820008u,bl(N+12,D),0x4e800020u});
    put(D,{0x3860002au,0x4e800020u});
    for(unsigned r=0;r<32;++r)c.gpr[r]=0x12340000u+r;
    c.gpr[1]=Frame+0x1000u;c.gpr[11]=Frame;c.gpr[7]=0xcd006434u;c.gpr[8]=0xe0010300u;
    c.gpr[9]=mode=="deeper"?1u:0u;c.gpr[10]=mode=="nested"?c.gpr[7]:Frame+0x200u;
    c.gpr[12]=mode=="second"?c.gpr[7]:Frame+0x100u;
    c.pc=H;c.lr=0x80008000u;c.msr=0x32u;c.is_running=true;c.dispatch_saved_ctx=0;
    for(unsigned i=1;i<=4;++i)c.mmu.write32(Frame-4*i,0xdeadbeefu);
    run_game(c);throw std::runtime_error("V694 bounded observer failed to terminate");
}
