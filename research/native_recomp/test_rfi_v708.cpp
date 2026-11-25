#include "runtime/cpu_context.h"
#include "wii_native_pi_exception_v545.h"
#include "wii_external_return_v706.h"
#include "wii_si_type_scheduler_v514.h"
#include "rfi_test_v708.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t Entry=0x80004000u,Resume=Entry+12u,Stop=Entry+16u,Other=0x100u,Rfi=ExternalVector+18*4u;
constexpr unsigned VectorBytes=19*4u;
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(!ok)throw std::runtime_error("V708 return assertion line "+std::to_string(loc.line()));
}
static ExternalReturnWitness witness;
static std::atomic<uint32_t> cause{Other},mask{8u};
namespace rfi_test {
void before(nwii::runtime::CPUContext& c,uint32_t pc,uint32_t word){
    if(pc==Rfi)need(witness.before_rfi(c,pc,word,cause.load(),mask.load()));
    else {need(pc==Resume);need(witness.resume(c,pc,word,cause.load(),mask.load()));}
}}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static NativeIosTransport* transport=nullptr;
static SiController* si=nullptr;
static std::array<uint8_t,VectorBytes> installed{};
static unsigned deliveries=0,vectors=0,stops=0,writes=0;
void trace_call(uint32_t pc,CPUContext&){
    if(pc==ExternalVector)++vectors;
    else need(pc==Entry);
}
bool process_pending_callbacks(CPUContext& c){
    if(witness.stage()==2||witness.stage()==3){need(witness.poll(c,cause.load(),mask.load()));return false;}
    if(witness.stage()==0&&(c.msr&0x8000u)&&(cause.load()&mask.load())){
        need(witness.capture(c,cause.load(),mask.load()));
        need(enter_native_pi_irq(c,*transport,installed,SiController::PI_SI,true)==ExternalEntry::Entered);
        ++deliveries;return true;
    }
    need(witness.stage()<=1);return false;
}
bool handle_syscall(CPUContext& c){
    need(c.pc==Stop&&witness.stage()==5);++stops;c.is_running=false;return true;
}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null call");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}void GX_WGPIPE_Write16(uint16_t){}void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected MMIO16");}
uint32_t HW_Reg_Read32(uint32_t){throw std::runtime_error("unexpected MMIO read");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected MMIO16");}
void HW_Reg_Write32(uint32_t a,uint32_t value){
    need(si&&(a==0x0d006434u||a==0x0d006438u));
    si->write(a-0x0d006400u,value);++writes;
}}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char** argv){
    using namespace nwii::runtime;using Port=SiTypeScheduler::Port;
    need(argc==2);std::ifstream raw(argv[1],std::ios::binary);
    raw.read(reinterpret_cast<char*>(installed.data()),installed.size());
    need(raw.gcount()==std::streamsize(installed.size())&&raw.peek()==std::char_traits<char>::eof());
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    for(unsigned i=0;i<installed.size();++i)c.mmu.write8(ExternalVector+i,installed[i]);
    c.mmu.write32(Resume,0x38a50001u);
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,cause,mask);transport=&ios;
    for(unsigned trial=0;trial<16;++trial){
        witness=ExternalReturnWitness{};cause=Other;mask=8;
        SiController ctl(cause);si=&ctl;
        SiTypeScheduler sched(ctl,{Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
        ctl.write(SiController::Control,0xc0010301u);sched.advance(1);sched.advance(9);
        need(cause==(Other|8u));
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        for(unsigned i=0;i<8;++i){
            c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);
            c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);
        }
        c.gpr[1]=0x80010000u+trial*0x100u;c.gpr[5]=0;
        c.pc=Entry;c.lr=Stop;c.msr=0;c.ctr=trial+7;c.xer=0x80000000u|trial;
        c.srr0=0x11223344u;c.srr1=0x55667788u;c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=100;
        run_game(c);
        need(!c.is_running&&witness.stage()==5&&c.gpr[5]==1&&cause==Other&&mask==8&&ctl.read(SiController::Status)==0);
    }
    need(deliveries==16&&vectors==16&&stops==16&&writes==32&&ios.serviced_steps()==0);
    std::cout<<"V708_RFI_AOT cases=16 native_entry=16 guest_ack=16 integer_context=16 native_resume=16 fallback=0 original_execution=0\n";
}
