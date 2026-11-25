#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_callback_prefix.h"
#include "wii_callback_return_v846.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using undercover::wii::HandlerNativeReturnWitness;
using undercover::wii::HandlerReturnExpectation;
constexpr uint32_t Stack=0x80022000u,Back=H+4u,MSR=0x32u;
static constexpr std::array<uint32_t,4> tail{prefix_words[1],prefix_words[2],prefix_words[3],prefix_words[4]};
static HandlerNativeReturnWitness witness(HandlerReturnExpectation{C,S,Back,save_words,tail,caller_words[1]});
static std::array<uint32_t,32> original{};
static unsigned entries=0,visits=0,outer=0;
static uint64_t tick=100;
static uint32_t ctr=0,xer=0,cr=0;
static bool corrupt=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V879_TAIL_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits
       <<" outer="<<outer<<" witness="<<witness.failure()<<" stage="<<witness.stage()<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static uint32_t pack(CPUContext& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
static bool held(CPUContext& c){return c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.ctr==ctr&&c.xer==xer&&pack(c)==cr;}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick&&c.mmu.read32(pc)==w&&held(c));++visits;
    if(pc==H){need(entries==1&&visits==1&&outer==1&&w==0x4e800421u);return;}
    if(pc==C){need(entries==2&&witness.start_dispatch(c,pc,w,original,cr,true));return;}
    if(corrupt&&pc==S){
        need(!witness.before(c,pc,w,true)&&witness.failure()==4u);
        std::cout<<"V879_TAIL_REFUSAL saved_gpr_corruption=1"<<std::endl;std::_Exit(126);
    }
    need(witness.before(c,pc,w,true));
    if(pc==Back){
        need(!corrupt&&entries==3&&outer==3&&witness.stage()==5u&&witness.visits()==21u&&c.gpr[1]==Stack);
        for(unsigned i=14;i<32;++i)need(c.gpr[i]==original[i]);
        std::cout<<"V879_OWNER_HANDLER_TAIL restore_gprs=15 tail_words=4 original_return=1 outer_dispatch=1 abi=1 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
}
void dispatch_resume(CPUContext& c,uint32_t pc,uint32_t w){
    need(pc==Back&&outer==3&&c.inst_count==++tick&&held(c)&&witness.dispatch_resume(c,pc,w,true));
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,3> order{H,C,S};
    need(entries<order.size()&&pc==order[entries]&&c.pc==pc&&held(c));
    if(entries<2){need(c.inst_count==tick+1u&&outer==entries+1u);++tick;}
    else need(c.inst_count==tick&&witness.entry(c,pc,true));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    need(c.inst_count==tick&&held(c));
    if(outer==0)need(c.pc==H&&visits==0);
    else if(outer==1)need(c.pc==C&&visits==1);
    else if(outer==2)need(c.pc==Back&&witness.dispatch_poll(c,true));
    else fail(2);
    ++outer;return false;
}
bool handle_syscall(CPUContext&){fail(3);}
void interpret_step(CPUContext&){fail(4);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}
void note_null_call(uint32_t,uint32_t){fail(5);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}uint32_t HW_Reg_Read32(uint32_t){fail(7);}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}void HW_Reg_Write32(uint32_t,uint32_t){fail(7);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==3);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    const unsigned trial=unsigned(std::stoul(argv[2]));need(trial<8);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller_words);put(C,prefix_words);put(S,save_words);
    for(unsigned i=0;i<32;++i)original[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    original[1]=Stack;original[2]=0x80025000u;original[13]=0x8070e8e0u;
    c.gpr=original;c.gpr[1]=Stack-FrameSize;
    if(SaveBase==11u)c.gpr[11]=Stack;
    const uint32_t frame=c.gpr[SaveBase];
    for(unsigned i=17;i<32;++i){
        c.gpr[i]^=0xdeadbeefu;
        c.mmu.write32(frame+SaveDisp+4u*(i-17u),original[i]^(corrupt&&i==17u?1u:0u));
    }
    c.mmu.write32(c.gpr[1]+LinkOffset,Back);
    for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
    cr=pack(c);ctr=c.ctr=C;xer=c.xer=0x80000000u|trial;
    c.pc=H;c.lr=0x80007000u;c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=tick;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    run_game(c);fail(8);
}catch(...){fail(8);}
