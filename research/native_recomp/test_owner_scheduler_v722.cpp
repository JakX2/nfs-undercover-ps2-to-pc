#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_scheduler_input.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t Sda=0x80020000u,Counter=Sda+CounterDisp,Hint=Sda+HintDisp,MSR=0x32u;
static std::array<uint32_t,32> gp;
static unsigned entries=0,visits=0,outer=0,stops=0,stage=0,initial=0;
static uint64_t last=0;
static bool request_switch=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<"V722_SCHEDULER_FAULT kind="<<kind<<" line="<<line<<" stage="<<stage
             <<" entries="<<entries<<" visits="<<visits<<" outer="<<outer<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)fail(1,loc.line());
}
static bool abi(CPUContext& c){
    if(c.gpr[1]!=gp[1]||c.gpr[2]!=gp[2]||c.gpr[13]!=gp[13]||c.msr!=MSR)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp[i])return false;
    return true;
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t word){
    // The synthetic stop can be followed by a native blr label; no guest
    // scheduler or original context is allowed to execute after stopping.
    if(!c.is_running){need(pc==H+16u&&stage==3);return;}
    need(!(c.msr&0x8000u)&&!c.in_callback&&!c.dispatch_saved_ctx&&c.mmu.read32(pc)==word);
    if(visits)need(c.inst_count-last==1);
    last=c.inst_count;need(++visits<=128);
    if(pc==H){need(stage==0&&entries==1&&abi(c));stage=1;return;}
    if(pc==H+4u){
        if(c.gpr[3]!=initial||c.mmu.read32(Counter)!=initial-1u){
            std::cout<<"V722_SCHEDULER_MISMATCH return="<<unsigned(c.gpr[3]!=initial)
                     <<" counter="<<unsigned(c.mmu.read32(Counter)!=initial-1u)<<std::endl;fail(2);
        }
        need(stage==1&&entries==4&&c.lr==pc&&abi(c));stage=2;return;
    }
    if(pc==H+8u){
        need(!request_switch&&stage==2&&entries==5&&c.lr==pc&&abi(c)&&c.mmu.read32(Counter)==initial-1u&&c.mmu.read32(Hint)==0);
        stage=3;return;
    }
    if(pc==H+12u){need(stage==3);return;}
    need(stage==1?((pc>=E&&pc<E+4*enable_words.size())||(pc>=D&&pc<D+4*disable_words.size())||(pc>=R&&pc<R+4*restore_words.size())):
        stage==2&&pc>=S&&pc<S+4*resched_words.size());
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,6> order{H,E,D,R,S,G};
    need(entries<order.size()&&pc==order[entries]&&c.pc==pc);++entries;
    if(pc==G){
        need(request_switch&&stage==2&&entries==6&&c.gpr[3]==0&&c.mmu.read32(Counter)==initial-1u);
        std::cout<<"V722_SWITCH_REFUSAL guarded_tail=1 original_switch=0"<<std::endl;std::_Exit(126);
    }
}
bool process_pending_callbacks(CPUContext& c){
    if(!outer&&c.pc==H&&!visits&&c.msr==MSR){++outer;return false;}
    if(request_switch&&stage==2&&entries==5&&c.pc==G&&c.msr==MSR)return false;
    fail(3);
}
bool handle_syscall(CPUContext& c){
    need(c.pc==H+12u&&stage==3&&entries==5&&!request_switch);++stops;c.is_running=false;return true;
}
void interpret_step(CPUContext&){fail(4);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(5);}
void note_null_call(uint32_t,uint32_t){fail(6);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(7);}void GX_WGPIPE_Write16(uint16_t){fail(7);}void GX_WGPIPE_Write32(uint32_t){fail(7);}
void GX_WGPIPE_WriteF32(float){fail(7);}void GX_WGPIPE_WriteF64(double){fail(7);}
uint16_t HW_Reg_Read16(uint32_t){fail(8);}uint32_t HW_Reg_Read32(uint32_t){fail(8);}
void HW_Reg_Write16(uint32_t,uint16_t){fail(8);}void HW_Reg_Write32(uint32_t,uint32_t){fail(8);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==2);std::string mode=argv[1];need(mode=="valid"||mode=="switch");request_switch=mode=="switch";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller);put(E,enable_words);put(S,resched_words);put(D,disable_words);put(R,restore_words);put(G,guard_words);
    for(unsigned trial=0;trial<(request_switch?1u:6u);++trial){
        entries=visits=outer=stage=0;initial=trial+1;
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80040000u+trial*0x100u;c.gpr[2]=0x80025000u;c.gpr[13]=Sda;gp=c.gpr;
        c.mmu.write32(Counter,initial);c.mmu.write32(Hint,request_switch?1u:0u);
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80009000u;c.srr1=0x8032u;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;c.inst_count=100;
        run_game(c);
        need(!request_switch&&!c.is_running&&stage==3&&entries==5&&outer==1&&stops==trial+1&&abi(c));
    }
    std::cout<<"V722_OWNER_SCHEDULER_AOT valid=6 original_enable=6 original_resched=6 original_switch=0 fallback=0 continuous_boot=0\n";
}catch(...){fail(9);}
