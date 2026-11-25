#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_pair_input.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t Frame=0x80020000u,MSR=0x32u,First=32-Count,RestoreCall=H+4*(Count+1),Resume=RestoreCall+4;
static std::array<uint32_t,32> saved{};
static unsigned entries=0,visits=0,outer=0,stops=0,stage=0,index_=0;
static uint64_t last=0;
static uint32_t frame=0,cr=0,xer=0,ctr=0;
static bool corrupt=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V753_PAIR_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits<<" stage="<<stage<<std::endl;
    std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static uint32_t pack_cr(CPUContext& c){
    uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
    return v;
}
static void state(CPUContext& c,unsigned written,unsigned clobbered,unsigned restored){
    need(c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.ctr==ctr&&c.xer==xer&&pack_cr(c)==cr&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    for(unsigned i=0;i<32;++i){
        uint32_t expected=(i>=First&&i<First+clobbered&&i>=First+restored)?0x1234u:saved[i];
        if(corrupt&&restored==1&&i==First){
            need(c.gpr[i]==(expected^1u));
            std::cout<<"V753_PAIR_REFUSAL corrupted_saved_register=1"<<std::endl;std::_Exit(126);
        }
        need(c.gpr[i]==expected);
    }
    for(unsigned i=0;i<Count;++i)need(c.mmu.read32(frame+Disp+4*i)==(i<written?(saved[First+i]^(corrupt&&stage>=3&&i==0?1u:0u)):0xdeadbeefu));
    need(c.mmu.read32(frame+Disp-4)==0x12345678u&&c.mmu.read32(frame+Disp+4*Count)==0x87654321u);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    if(stage==5){need(pc==Resume+4&&!c.is_running);return;}
    if(visits)need(c.inst_count-last==1u);
    last=c.inst_count;++visits;need(c.mmu.read32(pc)==w);
    if(pc==H){need(stage==0&&entries==1&&w==caller_words[0]);state(c,0,0,0);stage=1;index_=0;return;}
    if(stage==1){
        need(entries==2&&index_<=Count&&pc==S+4*index_&&w==save_words[index_]&&c.lr==H+4);
        state(c,index_,0,0);if(index_++==Count){stage=2;index_=0;}return;
    }
    if(stage==2){
        need(entries==2&&pc==H+4*(index_+1)&&w==caller_words[index_+1]&&c.lr==H+4);
        state(c,Count,index_,0);
        if(index_++==Count){
            if(corrupt)c.mmu.write32(frame+Disp,saved[First]^1u);
            stage=3;index_=0;
        }
        return;
    }
    if(stage==3){
        need(entries==3&&index_<=Count&&pc==R+4*index_&&w==restore_words[index_]&&c.lr==Resume);
        state(c,Count,Count,index_);if(index_++==Count)stage=4;return;
    }
    need(stage==4&&pc==Resume&&entries==3&&c.lr==Resume&&w==0x60000000u);
    state(c,Count,Count,Count);stage=5;++stops;c.is_running=false;
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    const std::array<uint32_t,3> order{H,S,R};
    need(c.pc==pc&&entries<order.size()&&pc==order[entries]);++entries;
}
bool process_pending_callbacks(CPUContext& c){need(!outer&&!visits&&c.pc==H&&c.msr==MSR);++outer;return false;}
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
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& words){for(auto w:words){c.mmu.write32(a,w);a+=4;}};
    put(H,caller_words);put(S,save_words);put(R,restore_words);
    for(unsigned trial=0;trial<(corrupt?1u:8u);++trial){
        entries=visits=outer=stage=index_=0;frame=Frame+0x100u*trial;
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=Frame+0x2000u;c.gpr[SaveBase]=frame;c.gpr[RestoreBase]=frame;saved=c.gpr;
        for(unsigned i=0;i<Count;++i)c.mmu.write32(frame+Disp+4*i,0xdeadbeefu);
        c.mmu.write32(frame+Disp-4,0x12345678u);c.mmu.write32(frame+Disp+4*Count,0x87654321u);
        for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
        cr=pack_cr(c);ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=100;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;run_game(c);
        need(!corrupt&&!c.is_running&&stage==5&&entries==3&&visits==3*Count+5&&outer==1&&stops==trial+1);
    }
    std::cout<<std::dec<<"V753_OWNER_PAIR_AOT valid=8 native_save=8 native_restore=8 gprs="<<Count<<" fallback=0 continuous_boot=0"<<std::endl;
}catch(...){fail(8);}
