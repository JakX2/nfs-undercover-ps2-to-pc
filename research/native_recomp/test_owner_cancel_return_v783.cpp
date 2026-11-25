#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_head_input.h"
#include "wii_alarm_cancel_return_v782.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
constexpr uint32_t Sda=0x8070e8e0u,Head=Sda-3496u,Tail=Sda-3492u,MSR=0x32u;
constexpr uint32_t A=0x80030000u,B=A+0x100u,N=B+0x100u,Handler=0x80050000u;
static AlarmCancelExpectation expectation(){
    AlarmCancelExpectation e{H,caller[0],C,C+4u*uint32_t(cancel_words.size()),T,K,Head,Tail,{},{}};
    for(unsigned i=0;i<7;++i)e.root_calls[i]={cancel_sites[i],cancel_targets[i],cancel_ends[i],cancel_branches[i]};
    for(unsigned i=0;i<3;++i)e.time_calls[i]={leaf_sites[i],std::array<uint32_t,3>{D,U,R}[i],
        std::array<uint32_t,3>{D+4u*uint32_t(disable_words.size()),U+4u*uint32_t(time_words.size()),R+4u*uint32_t(restore_words.size())}[i],leaf_branches[i],i+1u};
    return e;
}
static AlarmCancelReturnWitness route(expectation());
static unsigned trial=0,lane=0,visits=0,entries=0,outer=0,stops=0;
static std::string mode;
static std::array<unsigned,5> passed{};
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V783_FAULT kind="<<kind<<" line="<<line<<" lane="<<lane<<" visits="<<visits
      <<" stage="<<route.stage()<<" route="<<route.failure()<<" queue="<<route.queue_failure()<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    if(!c.is_running){need(pc==H+8u);return;}
    ++visits;need(visits<=258u);
    if(pc==H){need(entries==1&&route.start(c,pc,w,true)&&route.lane()==lane);return;}
    if(pc==H+4u){
        if(mode=="gpr")c.gpr[14]^=1u;
        if(mode=="link")c.mmu.write32(N+16u,B);
        if(mode=="tick")++c.inst_count;
        const bool ok=route.returned(c,pc,w,true);
        if(mode!="valid"){
            need(!ok&&route.failure()==8);
            std::cout<<"V783_REFUSAL kind="<<(mode=="gpr"?1:mode=="link"?2:3)<<std::endl;std::_Exit(126);
        }
        need(ok&&route.stage()==4&&route.total()==visits-2u);
        need(route.timer_required()==(lane==4));
        const unsigned calls=route.calls();
        need((calls&1u)&&((calls&66u)==2u||(calls&66u)==64u));
        if(lane==4)need((calls&4u)&&((calls&56u)==8u||(calls&56u)==16u||(calls&56u)==32u)&&entries==9);
        else need(!(calls&60u)&&entries==4);
        ++passed[lane];++stops;c.is_running=false;return;
    }
    need(route.native_before(c,pc,w,true));
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(!entries)need(pc==H&&c.pc==pc);else need(route.entry(c,pc,true));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(!visits){need(!outer&&c.pc==H);++outer;return false;}
    need(route.poll(c,true));return false;
}
bool handle_syscall(CPUContext&){fail(2);}
void interpret_step(CPUContext&){fail(3);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}
void note_null_call(uint32_t,uint32_t){fail(5);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}uint32_t HW_Reg_Read32(uint32_t){fail(7);}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}void HW_Reg_Write32(uint32_t,uint32_t){fail(7);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==2);mode=argv[1];need(mode=="valid"||mode=="gpr"||mode=="link"||mode=="tick");
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller);put(C,cancel_words);put(D,disable_words);put(R,restore_words);put(T,system_words);put(U,time_words);put(K,timer_words);
    for(trial=0;trial<(mode=="valid"?14u:1u);++trial){
        lane=trial<8?trial%4:4;
        entries=visits=outer=0;route=AlarmCancelReturnWitness(expectation());
        auto wr=[&](uint32_t a,uint32_t v){c.mmu.write32(a,v);};
        const uint64_t deadline=trial%3==0?0u:trial%3==1?100000u:0x100000000ull;
        for(auto a:{A,B,N}){
            for(unsigned i=0;i<10;++i)wr(a+4*i,0xcafe0000u+trial+i);
            wr(a,Handler);wr(a+8,uint32_t(deadline>>32));wr(a+12,uint32_t(deadline));wr(a+16,0);wr(a+20,0);
            wr(a-4,0xabcdef01u);wr(a+40,0x10fedcbau);
        }
        wr(Head,A);wr(Tail,N);
        if(lane==0){wr(B,0);wr(A+20,N);wr(N+16,A);}
        if(lane==1){wr(A+20,B);wr(B+16,A);wr(B+20,N);wr(N+16,B);}
        if(lane==2){wr(Tail,B);wr(A+20,B);wr(B+16,A);}
        if(lane==3){wr(Head,B);wr(Tail,B);}
        if(lane==4){wr(Head,B);wr(B+20,N);wr(N+16,B);}
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80040000u+trial*0x100u;c.gpr[2]=0x80025000u;c.gpr[13]=Sda;c.gpr[3]=B;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80009000u;c.srr1=0x8032u;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;c.inst_count=100+trial*1000;
        c.dec_value=0xffffffffu;c.dec_irq_pending=false;c.dec_written_tb=0;
        run_game(c);need(mode=="valid"&&!c.is_running&&outer==1&&stops==trial+1);
        for(auto a:{A,B,N})need(c.mmu.read32(a-4)==0xabcdef01u&&c.mmu.read32(a+40)==0x10fedcbau);
    }
    need(passed==std::array<unsigned,5>{2,2,2,2,6});
    std::cout<<"V783_OWNER_CANCEL_RETURN valid=14 inactive=2 middle=2 tail=2 singleton=2 head=6 fallback=0 continuous_boot=0\n";
}catch(...){fail(8);}
