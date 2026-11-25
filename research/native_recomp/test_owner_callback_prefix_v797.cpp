#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_callback_prefix.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t Stack=0x80022000u,Low=Stack-0x400u,High=Stack+0x100u,MSR=0x32u;
static std::array<uint32_t,32> gp{};
static std::array<uint32_t,(High-Low)/4> stack{};
static uint32_t lr=0,ctr=0,xer=0,cr=0,next=H;
static uint64_t tick=100;
static unsigned entries=0,visits=0,outer=0,writes=0;
static bool corrupt=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V797_PREFIX_FAULT kind="<<kind<<" line="<<line
      <<" entries="<<entries<<" visits="<<visits<<" writes="<<writes<<std::endl;
    std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static uint32_t pack(CPUContext& c){
    uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
    return v;
}
static void store(uint32_t a,uint32_t v){
    need(a>=Low&&a<High&&!(a&3u));
    stack[(a-Low)/4]=v;++writes;
}
static void state(CPUContext& c){
    need(c.gpr==gp&&c.lr==lr&&c.ctr==ctr&&c.xer==xer&&pack(c)==cr&&
        c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    for(unsigned i=0;i<stack.size();++i){
        if(c.mmu.read32(Low+4*i)!=stack[i]){
            if(corrupt&&next==Resume){
                std::cout<<"V797_PREFIX_REFUSAL saved_word_corruption=1"<<std::endl;std::_Exit(126);
            }
            fail(2);
        }
    }
}
static void reference(uint32_t pc,uint32_t w){
    const unsigned op=w>>26,xo=(w>>1)&1023,rd=(w>>21)&31,ra=(w>>16)&31,rb=(w>>11)&31;
    const uint32_t d=((w&0xffffu)^0x8000u)-0x8000u;
    next=pc+4;
    if(op==36||op==37){
        const uint32_t a=(ra?gp[ra]:0u)+d;
        store(a,gp[rd]);if(op==37)gp[ra]=a;
    }else if(op==14)gp[rd]=(ra?gp[ra]:0u)+d;
    else if(op==31&&xo==339){need((ra|(rb<<5))==8u);gp[rd]=lr;}
    else if(op==31&&xo==444)gp[ra]=gp[rd]|gp[rb];
    else if(w==0x60000000u){}
    else if(op==18&&(w&3u)==1u){
        lr=pc+4;next=pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u);
        need((pc==H&&next==C)||(pc==SaveCall&&next==S));
    }else if(w==0x4e800020u){need(pc==S+24&&lr==Resume);next=lr;}
    else fail(3);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick);
    need(pc==next);
    need(c.mmu.read32(pc)==w);
    ++visits;need(visits<=32);
    if(pc==Resume&&corrupt){
        const uint32_t a=gp[SaveBase]+uint32_t(SaveDisp);
        c.mmu.write32(a,c.mmu.read32(a)^1u);
    }
    state(c);
    if(pc==Resume){
        need(!corrupt&&entries==3&&outer==1&&writes==8&&visits==prefix_words.size()+7);
        std::cout<<"V797_OWNER_CALLBACK_PREFIX original_prologue=1 save_return=1 stack_writes=8 continuation_executed=0 fallback=0 continuous_boot=0"<<std::endl;
        std::_Exit(0);
    }
    reference(pc,w);
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,3> order{H,C,S};
    need(c.pc==pc&&entries<order.size()&&pc==order[entries]);
    // The pinned dispatcher increments inst_count once before the first
    // function entry. Subsequent direct calls do not re-enter the dispatcher.
    if(entries==0){need(outer==1&&c.inst_count==tick+1u);++tick;}
    else need(c.inst_count==tick);
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){need(!outer&&!visits&&c.pc==H&&c.inst_count==tick);++outer;return false;}
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
    need(argc==3);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    unsigned trial=unsigned(std::stoul(argv[2]));need(trial<8);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller_words);put(C,prefix_words);put(S,save_words);
    for(unsigned i=0;i<stack.size();++i){stack[i]=0xdeadbeefu^(trial*0x9e3779b9u+i);c.mmu.write32(Low+4*i,stack[i]);}
    for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    c.gpr[1]=Stack;c.gpr[2]=0x80025000u;c.gpr[13]=0x8070e8e0u;c.gpr[3]=trial%4;
    gp=c.gpr;
    for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
    cr=pack(c);ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
    c.pc=H;lr=c.lr=0x80007000u;c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=tick;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    run_game(c);fail(8);
}catch(...){fail(8);}
