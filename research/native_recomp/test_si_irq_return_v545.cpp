#include "runtime/cpu_context.h"
#include "wii_native_pi_exception_v545.h"
#include "wii_si_type_scheduler_v514.h"
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t Entry=0x80004000u,Resume=Entry+12u,Stop=Entry+16u,Other=0x100u;
constexpr unsigned VectorBytes=17u*4u;
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(!ok)throw std::runtime_error("native SI exception line "+std::to_string(loc.line()));
}
template<class F>static void reject(F f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught);}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
static unsigned entries=0,vectors=0,deliveries=0,stops=0,writes=0;
static NativeIosTransport* transport=nullptr;
static SiController* si=nullptr;
static std::array<uint8_t,VectorBytes> installed{};
void trace_call(uint32_t pc,CPUContext&){
    if(pc==Entry)++entries;else if(pc==ExternalVector)++vectors;
    else if(pc!=Stop)throw std::runtime_error("unexpected entry");
}
bool process_pending_callbacks(CPUContext& c){
    need(transport&&si);
    auto entry=enter_native_pi_irq(c,*transport,installed,SiController::PI_SI,true);
    if(entry==ExternalEntry::Deferred)throw std::runtime_error("unresumable guest boundary");
    if(entry==ExternalEntry::Entered){
        need(c.srr0==Resume&&c.gpr[5]==0&&c.gpr[6]==0);
        ++deliveries;return true;
    }
    return false;
}
bool handle_syscall(CPUContext& c){need(c.pc==Stop);++stops;c.is_running=false;return true;}
void interpret_step(CPUContext& c){throw std::runtime_error("interpreter forbidden at synthetic PC "+std::to_string(c.pc));}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("micro interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("unexpected read16");}
uint32_t HW_Reg_Read32(uint32_t a){
    need(si&&a>=0x0d006430u&&a<0x0d006500u);
    return si->read(a-0x0d006400u);
}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("unexpected write16");}
void HW_Reg_Write32(uint32_t a,uint32_t value){
    need(si&&(a==0x0d006434u||a==0x0d006438u));
    si->write(a-0x0d006400u,value);++writes;
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
int main(int argc,char** argv){
    using namespace nwii::runtime;using Port=SiTypeScheduler::Port;
    need(argc==2);
    std::ifstream raw(argv[1],std::ios::binary);
    raw.read(reinterpret_cast<char*>(installed.data()),installed.size());
    need(raw.gcount()==std::streamsize(installed.size())&&raw.peek()==std::char_traits<char>::eof());
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    for(unsigned i=0;i<installed.size();++i)c.mmu.write8(ExternalVector+i,installed[i]);
    std::atomic<uint32_t> cause{Other},mask{0};
    NativeIosTransport ios(c.mmu.mem1,c.mmu.mem2,cause,mask);
    transport=&ios;
    for(unsigned trial=0;trial<32;++trial){
        SiController ctl(cause);si=&ctl;
        SiTypeScheduler sched(ctl,{trial&1u?Port::present({0x12,0x34,0x56}):Port::absent(),Port::absent(),Port::absent(),Port::absent()},8);
        ctl.write(SiController::Buffer,0);
        const bool transfer=(trial%4u)!=0,enabled=(trial%4u)!=1,expect=transfer&&enabled;
        if(transfer){
            ctl.write(SiController::Control,0xc0010301u);sched.advance(1);sched.advance(9);
            need(sched.completed()==1&&cause==(Other|SiController::PI_SI));
        }
        mask=enabled?SiController::PI_SI:0u;
        c.pc=Entry;c.lr=Stop;c.msr=0;c.is_running=true;c.dispatch_saved_ctx=0;c.gpr[5]=c.gpr[6]=0;
        c.srr0=0x11223344u;c.srr1=0x55667788u;
        const unsigned before=writes;
        need(enter_native_pi_irq(c,ios,installed,SiController::PI_SI,true)==ExternalEntry::NotPending);
        run_game(c);
        need(!c.is_running&&c.gpr[5]==1&&c.gpr[6]==uint32_t(expect)&&c.msr==IosBus::MSR_EE);
        need(writes==before+2u*unsigned(expect));
        if(expect)need(c.srr0==Resume&&c.srr1==IosBus::MSR_EE&&cause==Other&&ctl.read(SiController::Status)==0&&
            !(ctl.read(SiController::Control)&SiController::TC_INT));
        else if(transfer)need(cause==(Other|SiController::PI_SI));
        need(ios.serviced_steps()==0);
        if(transfer&&!expect)ctl.write(SiController::Control,SiController::TC_INT);
        need(cause==Other);
    }
    // An actual pending SI source may not enter at an unsafe host boundary.
    SiController ctl(cause);si=&ctl;ctl.write(SiController::Control,0xc0010301u);
    ctl.complete(ctl.pending()->token,{},SiController::ERR_NOREP);
    c.pc=Entry;c.msr=IosBus::MSR_EE;c.srr0=0x12345678u;c.srr1=0x87654321u;mask=SiController::PI_SI;
    auto unchanged=[&]{need(c.pc==Entry&&c.msr==IosBus::MSR_EE&&c.srr0==0x12345678u&&c.srr1==0x87654321u);};
    need(enter_native_pi_irq(c,ios,installed,SiController::PI_SI,false)==ExternalEntry::Deferred);unchanged();
    c.dispatch_saved_ctx=0x80001234u;
    need(enter_native_pi_irq(c,ios,installed,SiController::PI_SI,true)==ExternalEntry::Deferred);unchanged();
    c.dispatch_saved_ctx=0;
    mask=Other|SiController::PI_SI;
    reject([&]{enter_native_pi_irq(c,ios,installed,SiController::PI_SI,true);});unchanged();
    mask=SiController::PI_SI;
    c.mmu.write8(ExternalVector,installed[0]^1u);
    reject([&]{enter_native_pi_irq(c,ios,installed,SiController::PI_SI,true);});unchanged();
    need(entries==32&&vectors==16&&deliveries==16&&stops==32&&writes==32);
    std::cout<<"PASS: 32 generated native mtmsr/rfi trials, 16 real SI IRQ deliveries and guest ACKs, strict vector and source guards, no interpreter\n";
}
