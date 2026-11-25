#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_indirect_callback.h"
#include "wii_callback_prefix_v800.h"
#include "wii_callback_identity_v796.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
constexpr auto prefix=[](){
    std::array<uint32_t,prefix_words.size()-1> p{};
    for(std::size_t i=0;i<p.size();++i)p[i]=prefix_words[i];
    return p;
}();
static CallbackPrefixWitness<prefix.size(),save_words.size()> route(C,S,prefix,save_words);
static unsigned entries=0,polls=0,visits=0;
static uint64_t first_tick=0;
static std::string mode;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V806_CALLBACK_FAULT kind="<<kind<<" line="<<line<<" stage="<<route.stage()
        <<" witness="<<route.failure()<<" entries="<<entries<<" polls="<<polls<<" visits="<<visits<<std::endl;
    std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    ++visits;need(visits<=32);
    if(pc==H){
        need(entries==1&&polls==1&&c.inst_count==first_tick+2&&w==0x4e800421u);
        if(mode=="identity")c.mmu.write32(C+4u*171u,c.mmu.read32(C+4u*171u)^1u);
        const auto identity=classify_callback_identity(c,pc,w,6,2,C,full_callback_words,std::array<uint32_t,2>{H,H+4u});
        const bool ok=route.start_dispatch(c,pc,w,identity==2,true);
        if(mode=="identity"||mode=="ctr"){
            need(!ok&&route.failure()==1&&identity==(mode=="identity"?4u:2u));
            std::cout<<"V806_CALLBACK_REFUSAL kind="<<(mode=="identity"?1:2)<<std::endl;std::_Exit(126);
        }
        need(ok);return;
    }
    if(pc==Resume&&mode=="corrupt"){
        const uint32_t a=c.gpr[SaveBase]+uint32_t(SaveDisp);
        c.mmu.write32(a,c.mmu.read32(a)^1u);
        need(!route.before(c,pc,w,true)&&route.failure()==3);
        std::cout<<"V806_CALLBACK_REFUSAL kind=3"<<std::endl;std::_Exit(126);
    }
    need(route.before(c,pc,w,true));
    if(pc==Resume){
        need(route.stage()==6&&route.writes()==8&&route.visits()==prefix.size()+save_words.size()&&entries==3&&polls==2);
        std::cout<<"V806_OWNER_INDIRECT_CALLBACK dispatch=1 original_prologue=1 save_return=1 stack_writes=8 continuation_executed=0 fallback=0 continuous_boot=0"<<std::endl;
        std::_Exit(0);
    }
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,3> order{H,C,S};
    need(entries<order.size()&&pc==order[entries]&&c.pc==pc);
    if(!entries)need(polls==1&&c.inst_count==first_tick+1u);
    else need(route.entry(c,pc,true));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(!polls)need(!entries&&!visits&&c.pc==H&&c.inst_count==first_tick);
    else need(polls==1&&entries==1&&visits==1&&route.dispatch_poll(c,true));
    ++polls;return false;
}
bool handle_syscall(CPUContext&){fail(4);}
void interpret_step(CPUContext&){fail(5);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(5);}
void note_null_call(uint32_t,uint32_t){fail(6);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(7);}void GX_WGPIPE_Write16(uint16_t){fail(7);}void GX_WGPIPE_Write32(uint32_t){fail(7);}
void GX_WGPIPE_WriteF32(float){fail(7);}void GX_WGPIPE_WriteF64(double){fail(7);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}uint32_t HW_Reg_Read32(uint32_t){fail(7);}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}void HW_Reg_Write32(uint32_t,uint32_t){fail(7);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==3);mode=argv[1];need(mode=="valid"||mode=="identity"||mode=="ctr"||mode=="corrupt");
    const unsigned trial=unsigned(std::stoul(argv[2]));need(trial<8);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller_words);put(C,full_callback_words);put(S,save_words);
    constexpr uint32_t Stack=0x80022000u;
    for(uint32_t a=Stack-0x400u;a<Stack+0x100u;a+=4u)c.mmu.write32(a,a^(trial*0x9e3779b9u));
    for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    c.gpr[1]=Stack;c.gpr[2]=0x80025000u;c.gpr[13]=0x8070e8e0u;c.gpr[3]=trial%4;
    for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
    c.ctr=C|(mode=="ctr"?3u:0u);c.xer=0x80000000u|trial;
    c.pc=H;c.lr=0x80007000u;c.msr=0x32u;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=first_tick=100+trial*100u;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    run_game(c);fail(8);
}catch(...){fail(8);}
