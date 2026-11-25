#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "wii_alarm_cancel_queue_v780.h"
#include "owner_cancel_input.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using undercover::wii::AlarmCancelQueueWitness;
static AlarmCancelQueueWitness queue_witness;
constexpr uint32_t Sda=0x8070e8e0u,Head=Sda-3496u,Tail=Sda-3492u,MSR=0x32u;
constexpr uint32_t A=0x80030000u,B=A+0x100u,N=B+0x100u,Handler=0x80050000u;
static std::array<uint32_t,32> gp;
static unsigned entries=0,visits=0,outer=0,stops=0,trial=0;
static uint64_t last=0;
static bool guard=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<"V781_CANCEL_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits<<" lane="<<trial%4<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static bool abi(CPUContext& c){
    if(c.gpr[1]!=gp[1]||c.gpr[2]!=gp[2]||c.gpr[13]!=gp[13]||c.msr!=MSR)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp[i])return false;
    return true;
}
static void verify(CPUContext& c){
    auto rd=[&](uint32_t a){return c.mmu.read32(a);};
    const unsigned lane=trial%4;
    need(rd(B)==0&&rd(Head)==(lane==3?0:A)&&rd(Tail)==(lane==3?0:lane==2?A:N));
    need(rd(A)==Handler&&rd(N)==Handler);
    if(lane==0)need(rd(A+20)==N&&rd(N+16)==A);
    if(lane==1)need(rd(A+20)==N&&rd(N+16)==A);
    if(lane==2)need(rd(A+20)==0);
    for(auto addr:{A,B,N}){
        need(rd(addr-4)==0xabcdef01u&&rd(addr+40)==0x10fedcbau);
        for(unsigned off:{4u,8u,12u,24u,28u,32u,36u})need(rd(addr+off)==0xcafe0000u+off+trial);
    }
    need(rd(Head-4)==0x12345678u&&rd(Tail+4)==0x87654321u);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t word){
    if(!c.is_running){need(pc==H+8u);return;}
    need(!(c.msr&0x8000u)&&!c.in_callback&&!c.dispatch_saved_ctx&&c.mmu.read32(pc)==word);
    if(visits)need(c.inst_count-last==1);
    last=c.inst_count;need(++visits<=128);
    if(pc==H){need(entries==1&&abi(c));queue_witness=AlarmCancelQueueWitness{};need(queue_witness.capture(c,Head,Tail,c.gpr[3]));return;}
    if(pc==H+4u){
        need(!guard&&entries==4&&c.lr==pc&&abi(c));verify(c);need(queue_witness.finish(c)&&queue_witness.stage()==5);++stops;c.is_running=false;return;
    }
    need((pc>=C&&pc<C+4*cancel_words.size())||(pc>=D&&pc<D+4*disable_words.size())||(pc>=R&&pc<R+4*restore_words.size()));
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,4> order{H,C,D,R};
    need(c.pc==pc&&entries<order.size());
    if(std::find(guard_roots.begin(),guard_roots.end(),pc)!=guard_roots.end()){
        need(guard&&entries==3&&pc==T&&c.msr==MSR);
        std::cout<<"V781_HEAD_GUARD guarded_time=1 original_timer=0"<<std::endl;std::_Exit(126);
    }
    need(pc==order[entries]);++entries;
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
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="guard");guard=mode=="guard";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller);put(C,cancel_words);put(D,disable_words);put(R,restore_words);for(auto a:guard_roots)put(a,guard_words);
    for(trial=0;trial<(guard?1u:8u);++trial){
        entries=visits=outer=0;
        auto wr=[&](uint32_t a,uint32_t v){c.mmu.write32(a,v);};
        for(auto addr:{A,B,N}){
            wr(addr-4,0xabcdef01u);wr(addr+40,0x10fedcbau);wr(addr,Handler);
            for(unsigned off:{4u,8u,12u,24u,28u,32u,36u})wr(addr+off,0xcafe0000u+off+trial);
            wr(addr+16,0);wr(addr+20,0);
        }
        wr(Head-4,0x12345678u);wr(Tail+4,0x87654321u);
        const unsigned lane=trial%4;
        if(guard){wr(Head,B);wr(Tail,N);wr(B+20,N);wr(N+16,B);}
        else if(lane==0){wr(Head,A);wr(Tail,N);wr(A+20,N);wr(N+16,A);wr(B,0);}
        else if(lane==1){wr(Head,A);wr(Tail,N);wr(A+20,B);wr(B+16,A);wr(B+20,N);wr(N+16,B);}
        else if(lane==2){wr(Head,A);wr(Tail,B);wr(A+20,B);wr(B+16,A);}
        else {wr(Head,B);wr(Tail,B);}
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80040000u+trial*0x100u;c.gpr[2]=0x80025000u;c.gpr[13]=Sda;c.gpr[3]=B;gp=c.gpr;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80009000u;c.srr1=0x8032u;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;c.inst_count=100;run_game(c);
        need(!guard&&!c.is_running&&entries==4&&outer==1&&stops==trial+1&&abi(c));
    }
    std::cout<<"V781_OWNER_CANCEL_AOT valid=8 inactive=2 middle=2 tail=2 singleton=2 queue_witness=8 fallback=0 continuous_boot=0\n";
}catch(...){fail(8);}
