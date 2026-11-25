#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_timer_input.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t MSR=0x32u;
static std::array<uint32_t,32> gp;
static uint32_t cr=0,xer=0,ctr=0;
static uint64_t last=0,value=0,written=0;
static bool pending=false,corrupt=false;
static unsigned entries=0,visits=0,outer=0,stops=0,index_=0,stage=0;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V758_TIMER_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits<<" stage="<<stage<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static uint32_t pack_cr(CPUContext& c){
    uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
}
static void state(CPUContext& c){
    need(c.gpr==gp&&c.msr==MSR&&c.srr0==0x80009000u&&c.srr1==0x8032u&&c.ctr==ctr&&c.xer==xer&&pack_cr(c)==cr&&
         c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    if(corrupt&&stage==2&&index_==0){
        c.dec_value^=1u; // independent negative fixture, never part of original execution
        need(c.dec_value!=value);
        std::cout<<"V758_TIMER_REFUSAL timer_state_corruption=1"<<std::endl;std::_Exit(126);
    }
    need(c.dec_value==value&&c.dec_written_tb==written&&c.dec_irq_pending==pending);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    if(!c.is_running){need(pc==H+4*(targets.size()+1));return;}
    if(visits)need(c.inst_count-last==1u);
    last=c.inst_count;++visits;need(c.mmu.read32(pc)==w&&c.read_timebase()==c.inst_count);
    state(c);
    if(stage==0){
        need(pc==H+4*index_&&entries==index_+1&&w==caller[index_]);
        if(index_==targets.size()){++stops;c.is_running=false;return;}
        stage=1;return;
    }
    if(stage==1){
        need(pc==targets[index_]&&w==timer_words[index_][0]&&entries==index_+2&&c.lr==H+4*(index_+1));
        if(kinds[index_]==1){value=c.gpr[3];written=c.inst_count;pending=value!=0xffffffffu;}
        else {const auto elapsed=c.inst_count-written;gp[3]=elapsed>=value?0u:uint32_t(value-elapsed);}
        stage=2;return;
    }
    need(stage==2&&pc==targets[index_]+4&&w==0x4e800020u&&c.lr==H+4*(index_+1));
    ++index_;stage=0;
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc&&((entries==0&&pc==H)||(entries>0&&entries<=targets.size()&&pc==targets[entries-1])));++entries;
}
bool process_pending_callbacks(CPUContext& c){need(!outer&&!visits&&c.pc==H&&c.msr==MSR);++outer;return false;}
bool handle_syscall(CPUContext&){fail(2);}void interpret_step(CPUContext&){fail(3);}
void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}void note_null_call(uint32_t,uint32_t){fail(5);}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}uint32_t HW_Reg_Read32(uint32_t){fail(7);}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}void HW_Reg_Write32(uint32_t,uint32_t){fail(7);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller);for(unsigned i=0;i<targets.size();++i)put(targets[i],timer_words[i]);
    constexpr std::array<uint32_t,8> values{0,1,2,123,0x7fffffffu,0x80000000u,0xfffffffeu,0xffffffffu};
    for(unsigned trial=0;trial<(corrupt?1u:8u);++trial){
        entries=visits=outer=index_=stage=0;
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80040000u;c.gpr[3]=values[trial];gp=c.gpr;
        for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
        cr=pack_cr(c);ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80009000u;c.srr1=0x8032u;
        c.inst_count=100;c.dec_value=value=values[trial];c.dec_written_tb=written=80;c.dec_irq_pending=pending=value!=0xffffffffu;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;run_game(c);
        need(!corrupt&&!c.is_running&&entries==targets.size()+1&&index_==targets.size()&&visits==3*targets.size()+1&&outer==1&&stops==trial+1);
    }
    std::cout<<std::dec<<"V758_OWNER_TIMER_AOT valid=8 roots="<<targets.size()<<" native_returns=8 modeled_dec=1 irq_delivery=0 fallback=0 continuous_boot=0\n";
}catch(...){fail(8);}
