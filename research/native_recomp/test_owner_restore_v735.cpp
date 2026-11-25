#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_restore_input.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t Frame=0x80020000u,MSR=0x32u;
static std::array<uint32_t,32> initial{},wanted{};
static unsigned entries=0,visits=0,outer=0,stops=0;
static uint64_t last=0;
static uint32_t frame=0,cr=0,xer=0,ctr=0;
static bool corrupt=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<"V735_RESTORE_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits<<" outer="<<outer<<std::endl;
    std::_Exit(126);
}
static void need(bool ok,const std::source_location loc=std::source_location::current()){if(!ok)fail(1,loc.line());}
static uint32_t pack_cr(CPUContext& c){
    uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
    return v;
}
static void state(CPUContext& c,unsigned restored){
    need(c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.ctr==ctr&&c.xer==xer&&pack_cr(c)==cr&&
         c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    unsigned diff=0;
    for(unsigned i=0;i<32;++i)diff+=c.gpr[i]!=(i>=17&&i<17+restored?wanted[i]:initial[i]);
    if(corrupt&&restored==1){
        need(diff==1&&c.gpr[17]==(wanted[17]^1u));
        std::cout<<"V735_RESTORE_REFUSAL saved_gpr_corruption=1"<<std::endl;std::_Exit(126);
    }
    need(!diff);
    for(unsigned i=17;i<32;++i)need(c.mmu.read32(frame+Disp+4u*(i-17))==(wanted[i]^(corrupt&&i==17?1u:0u)));
    need(c.mmu.read32(frame+Disp-4u)==0x12345678u&&c.mmu.read32(frame+Disp+60u)==0x87654321u);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    if(visits)need(c.inst_count-last==1u);
    last=c.inst_count;
    if(pc==H){need(!visits&&entries==1&&w==resume_words[0]);state(c,0);++visits;return;}
    if(pc==H+4u){
        need(visits==17&&entries==2&&c.lr==H+4u&&w==resume_words[1]);state(c,15);++stops;c.is_running=false;
        std::cout<<"V735_RESTORE_TRIAL native_return=1 gpr_restores=15 guard_words=2"<<std::endl;return;
    }
    if(pc==H+8u){need(!c.is_running&&stops);return;}
    need(entries==2&&visits>=1&&visits<=16&&pc==L+4u*(visits-1u)&&w==loader_words[visits-1u]&&c.mmu.read32(pc)==w&&c.lr==H+4u);
    state(c,visits-1u);++visits;
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){need(c.pc==pc&&((entries==0&&pc==H)||(entries==1&&pc==L)));++entries;}
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
    put(H,resume_words);put(L,loader_words);
    for(unsigned trial=0;trial<(corrupt?1u:8u);++trial){
        entries=visits=outer=0;frame=Frame+0x100u*trial;
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=Frame+0x2000u;c.gpr[Base]=frame;initial=c.gpr;wanted=initial;
        for(unsigned i=17;i<32;++i){
            wanted[i]=initial[i]^0xdeadbeefu;c.mmu.write32(frame+Disp+4u*(i-17),wanted[i]^(corrupt&&i==17?1u:0u));
        }
        c.mmu.write32(frame+Disp-4u,0x12345678u);c.mmu.write32(frame+Disp+60u,0x87654321u);
        for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
        cr=pack_cr(c);ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;
        c.inst_count=100;c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;run_game(c);
        need(!corrupt&&!c.is_running&&entries==2&&visits==17&&outer==1&&stops==trial+1);
    }
    std::cout<<"V735_OWNER_RESTORE_AOT valid=8 original_restore=8 native_return=8 gprs=15 fallback=0 continuous_boot=0"<<std::endl;
}catch(...){fail(8);}
