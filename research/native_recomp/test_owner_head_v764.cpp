#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_head_input.h"
#include "wii_postack_os_leaf_v703.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using undercover::wii::PostAckOsLeaf;
constexpr uint32_t Sda=0x8070e8e0u,Head=Sda-3496u,Tail=Sda-3492u,MSR=0x32u;
constexpr uint32_t B=0x80030000u,N=B+0x100u,Handler=0x80050000u;
static std::array<uint32_t,32> gp{};
static std::array<PostAckOsLeaf,3> leaves{
    PostAckOsLeaf({leaf_sites[0],D,D+4u*uint32_t(disable_words.size()),leaf_branches[0],1}),
    PostAckOsLeaf({leaf_sites[1],U,U+4u*uint32_t(time_words.size()),leaf_branches[1],2}),
    PostAckOsLeaf({leaf_sites[2],R,R+4u*uint32_t(restore_words.size()),leaf_branches[2],3})};
static unsigned entries=0,visits=0,outer=0,stops=0,trial=0,leaf=0,time_visits=0,timer_visits=0,stage=0;
static uint64_t last=0,deadline=0,now=0,dec_tick=0;
static uint32_t expected_dec=0,timer_return=0,time_return=0;
static bool leaf_active=false,corrupt=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V764_HEAD_FAULT kind="<<kind<<" line="<<line<<" entries="<<entries<<" visits="<<visits<<" lane="<<trial%3<<" stage="<<stage<<" leaf="<<leaf<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static bool abi(CPUContext& c){
    if(c.gpr[1]!=gp[1]||c.gpr[2]!=gp[2]||c.gpr[13]!=gp[13]||c.msr!=MSR)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp[i])return false;
    return true;
}
static bool span(uint32_t pc,uint32_t base,size_t words){return pc>=base&&pc<base+4*words;}
static void queue(CPUContext& c){
    auto rd=[&](uint32_t a){return c.mmu.read32(a);};
    need(rd(B)==0&&rd(Head)==N&&rd(Tail)==N&&rd(N)==Handler&&rd(N+16)==0&&rd(N+20)==0);
    need(rd(N+8)==uint32_t(deadline>>32)&&rd(N+12)==uint32_t(deadline));
    for(auto addr:{B,N}){
        need(rd(addr-4)==0xabcdef01u&&rd(addr+40)==0x10fedcbau);
        for(unsigned off:{4u,24u,28u,32u,36u})need(rd(addr+off)==0xcafe0000u+off+trial);
    }
    need(rd(Head-4)==0x12345678u&&rd(Tail+4)==0x87654321u);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t word){
    if(!c.is_running){need(pc==H+8u);return;}
    need(c.msr==MSR&&!c.in_callback&&!c.dispatch_saved_ctx&&c.mmu.read32(pc)==word);
    if(visits)need(c.inst_count-last==1);
    last=c.inst_count;need(++visits<=256);
    if(pc==H){need(entries==1&&abi(c));return;}
    if(pc==H+4u){
        need(stage==5&&entries==9&&c.lr==pc&&abi(c)&&!leaf_active&&leaf==3&&time_visits==25&&timer_visits==2);
        queue(c);need(c.dec_value==expected_dec&&c.dec_written_tb==dec_tick&&c.dec_irq_pending);
        ++stops;c.is_running=false;return;
    }
    if(span(pc,T,system_words.size())){
        need(stage==2&&pc==T+4*time_visits++);
        if(leaf_active){
            need(leaf<3&&leaves[leaf].returned(c,pc));++leaf;leaf_active=false;
        }
        if(leaf<3&&pc==leaf_sites[leaf]){need(leaves[leaf].start(c,pc,word));leaf_active=true;}
        if(word==0x4e800020u){need(leaf==3&&time_visits==25&&c.lr==time_return);stage=3;}
        return;
    }
    if(leaf_active){need(leaf<3&&leaves[leaf].before(c,pc,word));return;}
    if(span(pc,C,cancel_words.size())){
        if(stage==3){
            need(pc==time_return);now=(uint64_t(c.gpr[3])<<32)|c.gpr[4];
            // Deadline comparison uses returned original system time, not host clock.
            expected_dec=deadline<=now?0u:deadline-now>0x7fffffffu?0x7fffffffu:uint32_t(deadline-now);
            stage=4;
        }
        if(pc==timer_return){need(timer_visits==2&&c.dec_value==expected_dec&&c.dec_written_tb==dec_tick&&c.dec_irq_pending);}
        return;
    }
    if(span(pc,K,timer_words.size())){
        need(stage==4&&timer_visits<2&&pc==K+4*timer_visits);
        if(!timer_visits){
            need(c.gpr[3]==expected_dec&&c.lr==timer_return);dec_tick=c.inst_count;
        }else{
            if(corrupt)c.dec_value^=1u;
            if(corrupt){need(c.dec_value!=expected_dec);std::cout<<"V764_TIMER_REFUSAL corrupted_dec=1"<<std::endl;std::_Exit(126);}
            need(c.dec_value==expected_dec&&c.dec_written_tb==dec_tick&&c.dec_irq_pending);
        }
        ++timer_visits;return;
    }
    need(span(pc,D,disable_words.size())||span(pc,R,restore_words.size()));
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,9> order{H,C,D,T,D,U,R,K,R};
    need(entries<order.size()&&pc==order[entries]&&c.pc==pc);
    if(entries==3){stage=2;time_return=c.lr;}
    if(entries>=4&&entries<=6)need(leaf_active&&leaf==entries-4&&leaves[leaf].entry(pc,c));
    if(entries==7){need(stage==4);timer_return=c.lr;}
    if(entries==8){need(timer_visits==2);stage=5;}
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(!visits){need(!outer&&c.pc==H&&c.msr==MSR);++outer;return false;}
    need(leaf_active&&leaf==1&&leaves[leaf].poll(c));return false;
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
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller);put(C,cancel_words);put(D,disable_words);put(R,restore_words);put(T,system_words);put(U,time_words);put(K,timer_words);
    for(trial=0;trial<(corrupt?1u:6u);++trial){
        entries=visits=outer=stage=leaf=time_visits=timer_visits=0;leaf_active=false;
        leaves={PostAckOsLeaf({leaf_sites[0],D,D+4u*uint32_t(disable_words.size()),leaf_branches[0],1}),
                PostAckOsLeaf({leaf_sites[1],U,U+4u*uint32_t(time_words.size()),leaf_branches[1],2}),
                PostAckOsLeaf({leaf_sites[2],R,R+4u*uint32_t(restore_words.size()),leaf_branches[2],3})};
        auto wr=[&](uint32_t a,uint32_t v){c.mmu.write32(a,v);};
        deadline=trial%3==0?0u:trial%3==1?100000u:0x100000000ull;
        for(auto addr:{B,N}){
            wr(addr-4,0xabcdef01u);wr(addr+40,0x10fedcbau);wr(addr,Handler);
            for(unsigned off:{4u,24u,28u,32u,36u})wr(addr+off,0xcafe0000u+off+trial);
            wr(addr+8,uint32_t(deadline>>32));wr(addr+12,uint32_t(deadline));wr(addr+16,0);wr(addr+20,0);
        }
        wr(Head-4,0x12345678u);wr(Tail+4,0x87654321u);
        wr(Head,B);wr(Tail,N);wr(B+20,N);wr(N+16,B);
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80040000u+trial*0x100u;c.gpr[2]=0x80025000u;c.gpr[13]=Sda;c.gpr[3]=B;gp=c.gpr;
        c.pc=H;c.lr=0x80006000u;c.msr=MSR;c.srr0=0x80009000u;c.srr1=0x8032u;
        c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;c.inst_count=100+trial*1000;
        c.dec_value=0xffffffffu;c.dec_irq_pending=false;c.dec_written_tb=0;run_game(c);
        need(!corrupt&&!c.is_running&&entries==9&&outer==1&&stops==trial+1&&abi(c));
        need(trial%3==0?expected_dec==0:trial%3==1?expected_dec>0&&expected_dec<0x7fffffffu:expected_dec==0x7fffffffu);
    }
    std::cout<<"V764_OWNER_HEAD_AOT valid=6 overdue=2 future=2 clamped=2 original_time=6 original_dec=6 fallback=0 continuous_boot=0\n";
}catch(...){fail(8);}
