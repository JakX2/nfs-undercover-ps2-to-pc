#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_restore_input.h"
#include "wii_postack_transfer_device_v771.h"
#include "wii_si_type_scheduler_v514.h"
#include "wii_handler_suffix_guard_v868.h"
#include <array>
#include <algorithm>
#include <bit>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
using Access=PostAckTransferDevice::Access;
constexpr uint32_t Bus=0xcd006400u,Other=0x100u,SI=SiController::PI_SI,MSR=0x32u;
constexpr unsigned C=SiController::Control,S=SiController::Status,B=SiController::Buffer;
static std::atomic<uint32_t> cause{Other},mask{SI};
static SiController ctl(cause);
static std::unique_ptr<SiTypeScheduler> scheduler;
static PostAckTransferDevice device;
static SiCompletionAckTrace ack;
static HandlerSuffixGuard guard;
static std::array<uint32_t,32> gp{};
static CPUContext* cpu=nullptr;
static uint64_t last=0;
static unsigned entries=0,outer=0,visits=0,reads=0,negative=0;
static uint32_t expected_status=0,expected_control=0;
static uint64_t tokens=0;
static constexpr auto labels=[]{
    std::array<HandlerSuffixLabel,7> r{};
    for(unsigned i=0;i<r.size();++i)r[i]={L+4*i,loader_words[i],0,0};
    return r;
}();
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<"V892_STATUS_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits
        <<" reads="<<reads<<" guard="<<guard.failure()<<" device="<<device.failure()<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)fail(1,l.line());}
static void advance(CPUContext& c){
    need(&c==cpu&&c.inst_count==last+1u);
    last=c.inst_count;scheduler->advance(last);
    need(device.after_return_at(c.inst_count)&&device.held_now()&&cause==(Other|SI)&&ctl.issued_tokens()==tokens);
}
static void reference(uint32_t w){
    const unsigned op=w>>26,xo=(w>>1)&1023u,rd=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
    if(op==15u)gp[rd]=(ra?gp[ra]:0u)+(uint32_t(w&0xffffu)<<16);
    else if(op==21u){
        const unsigned mb=(w>>6)&31u,me=(w>>1)&31u;uint32_t m=0;
        for(unsigned i=0;i<32;++i)if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))m|=1u<<(31u-i);
        gp[ra]=std::rotl(gp[rd],int(rb))&m;
    }else if(op==31u&&xo==792u){
        const unsigned sh=gp[rb]&63u;
        gp[ra]=uint32_t(std::bit_cast<int32_t>(gp[rd])>>std::min(sh,31u));
    }else if(op==32u){
        const uint32_t a=(ra?gp[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
        need(PostAckTransferDevice::offset(a)==S);
        gp[rd]=expected_status;
    }else fail(2);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    advance(c);need(c.mmu.read32(pc)==w&&c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    if(pc==H){need(entries==1&&outer==1&&visits==0&&c.gpr==gp);return;}
    need(entries==2&&pc==L+4*visits&&visits<7u);
    if(visits==0)need(guard.start(c,labels,pc));
    if(visits==6u&&negative==2u){
        c.gpr[(loader_words[5]>>21)&31u]^=1u;
        need(c.gpr!=gp);
        std::cout<<"V892_STATUS_REFUSAL kind=2"<<std::endl;std::_Exit(126);
    }
    need(c.gpr==gp&&guard.before(c,pc,w,0,0,visits==5u));
    if(visits==6u){
        need(reads==1u&&guard.visits()==7u&&guard.writes()==0u&&device.suffix_status_reads()==1u&&device.suffix_status_value()==expected_status&&
             ctl.read(S)==expected_status&&ctl.read(C)==expected_control&&scheduler->completed()==2u&&device.held_now());
        std::cout<<"V892_OWNER_STATUS_LOAD original_prefix=5 original_load=1 native_gpr=1 reads=1 writes=0 follow_held=1 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
    if(visits==5u){
        const auto a=PostAckTransferDevice::word_access(c,w);
        need(a.kind==Access::Read&&PostAckTransferDevice::offset(a.address)==S);
        if(negative!=1u)need(device.arm_suffix_status_read(c.inst_count,a.address));
    }
    reference(w);++visits;
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc&&((entries==0&&pc==H)||(entries==1&&pc==L)));
    if(!entries)advance(c);else need(c.inst_count==last);
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){need(!outer&&!entries&&c.inst_count==last&&device.held_now());++outer;return false;}
bool handle_syscall(CPUContext&){fail(3);}
void interpret_step(CPUContext&){fail(4);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}
void note_null_call(uint32_t,uint32_t){fail(5);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}
uint32_t HW_Reg_Read32(uint32_t a){
    need(cpu&&cpu->inst_count==last&&visits==6u&&!reads&&PostAckTransferDevice::offset(a)==S);
    uint32_t result=0;
    if(negative==1u){need(!device.read(ctl,S,result)&&device.failure()==8u);std::cout<<"V892_STATUS_REFUSAL kind=1"<<std::endl;std::_Exit(126);}
    need(device.read(ctl,S,result)&&result==expected_status&&device.held_now());++reads;return result;
}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}void HW_Reg_Write32(uint32_t,uint32_t){fail(7);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==3);const unsigned trial=unsigned(std::stoul(argv[1]));negative=unsigned(std::stoul(argv[2]));need(trial<8u&&negative<3u);
    auto c=std::make_unique<CPUContext>();cpu=c.get();
    const auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c->mmu.write32(a,w);a+=4u;}};
    put(H,resume_words);put(L,loader_words);
    using Port=SiTypeScheduler::Port;
    const auto port=(trial&4u)?Port::present({1,2,3}):Port::absent();
    const SiTypeScheduler::Profile ports{port,port,port,port};
    scheduler=std::make_unique<SiTypeScheduler>(ctl,ports,8);
    ctl.write(C,0xc0010301u);scheduler->advance(1);scheduler->advance(9);
    auto& tick=c->inst_count;tick=100;
    need(ack.arm(ctl,cause,mask,tick,H,H+16));++tick;need(ack.before(H,0x90030000u));
    ack.write(ctl,C,0xe0010300u);++tick;need(ack.before(H+4,0x60000000u)&&ack.resume_after_ack(H+4,0x60000000u));
    const unsigned ch=trial%4u;
    need(device.begin(ctl,cause,mask,ack,tick,ch,true,ports[ch].type,8));
    auto step=[&](Access a=Access::None,uint32_t address=0){scheduler->advance(++tick);return device.before(tick,a,address);};
    uint32_t result=0;
    need(step(Access::Read,Bus+C)&&device.read(ctl,C,result));
    need(step(Access::Write,Bus+B)&&device.write(ctl,B,0x00abcdefu));
    need(step(Access::Write,Bus+S)&&device.write(ctl,S,0x08000000u));
    need(step(Access::Write,Bus+C)&&device.write(ctl,C,0xc0010301u|(ch<<1)));
    for(unsigned i=0;i<9;++i)need(step());
    need(device.finish(tick,1)&&device.follow_stage()==3u&&device.held_now());
    last=tick;tokens=ctl.issued_tokens();expected_status=ctl.read(S);expected_control=ctl.read(C);
    for(unsigned i=0;i<32;++i)c->gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    c->gpr[1]=0x80022000u;c->gpr[2]=0x80025000u;c->gpr[13]=0x8070e8e0u;gp=c->gpr;
    c->pc=H;c->lr=0x80007000u;c->msr=MSR;c->srr0=0x80030000u;c->srr1=0x8032u;
    c->is_running=true;c->in_callback=false;c->dispatch_saved_ctx=0;
    run_game(*c);fail(8);
}catch(...){fail(8);}
