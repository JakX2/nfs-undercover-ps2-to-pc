#include "runtime/cpu_context.h"
#include "wii_external_return_v706.h"
#include "wii_live_epilogue_v762.h"
#include "rfi_test_v708.h"
#include "owner_epilogue_input.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using namespace undercover::wii;
using nwii::runtime::CPUContext;
constexpr uint32_t Context=0x80010000u,Other=0x100u,Mask=8u,Prior=0x8032u;
static ExternalReturnWitness witness,live_capture;
static LiveEpilogueWitness live({J,E,S,D,R,L,G,Context,CounterDisp,HintDisp,ContextReg,GqrMask});
static std::array<uint32_t,32> gp;
static std::array<uint32_t,8> gqr;
static uint32_t cr=0,lr=0,ctr=0,xer=0;
static uint32_t next_pc=0,alternate=0,poll_pc=0;
static uint64_t last_tick=0;
static unsigned visits=0,entries=0,outer=0,back_polls=0,stops=0;
static bool pending=false,corrupt=false,request_switch=false;
constexpr uint32_t Sda=0x80020000u,Counter=Sda+CounterDisp,Hint=Sda+HintDisp;
static std::array<uint32_t,32> scheduler_gp;
static unsigned sched_visits=0,sched_stage=0,initial=0;
static uint64_t sched_last=0;
static bool scheduler_abi(CPUContext& c){
    if(c.gpr[1]!=scheduler_gp[1]||c.gpr[2]!=scheduler_gp[2]||c.gpr[13]!=scheduler_gp[13]||c.msr!=0x32u)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=scheduler_gp[i])return false;
    return true;
}
[[noreturn]]static void fault(unsigned kind,unsigned line=0){
    std::cout<<"V737_CONTEXT_FAULT kind="<<kind<<" line="<<line<<" stage="<<witness.stage()
             <<" witness="<<witness.failure()<<" visits="<<visits<<" outer="<<outer
             <<" back_polls="<<back_polls<<std::endl;
    std::_Exit(126);
}
static void need(bool ok,const std::source_location loc=std::source_location::current()){
    if(!ok)fault(1,loc.line());
}
static uint32_t pack_cr(const CPUContext& c){
    uint32_t v=0;
    for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
    return v;
}
static unsigned gqr_diff(const CPUContext& c){
    unsigned n=0;for(unsigned i=0;i<8;++i)n+=c.gqr[i]!=gqr[i];return n;
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t word){
    if(pc==H){
        need(live.resume(c,pc,word,Other,Mask));
        need(sched_stage==4&&c.mmu.read32(Counter)==initial-1u&&!pending&&entries==7&&witness.resume(c,pc,word,Other,Mask));
        need(gqr_diff(c)==0&&c.mmu.read16(Context+0x1a2u)==0);
        return;
    }
    if(pc==J){
        const bool begun=live.begin(c,live_capture,Other,Mask);
        if(corrupt){need(!begun&&live.failure()==1);std::cout<<"V762_CONTEXT_REFUSAL saved_frame_corruption=1"<<std::endl;std::_Exit(126);}
        need(begun);
    }
    const bool live_ok=live.before(c,pc,word,Other,Mask);
    if(request_switch&&live.failure()==7){std::cout<<"V737_SWITCH_REFUSAL guarded_tail=1 original_switch=0"<<std::endl;std::_Exit(126);}
    if(!live_ok){std::cout<<std::dec<<"V762_EPILOGUE_INVALID reason="<<live.failure()<<" stage="<<live.stage()<<" visits="<<live.visits()<<std::endl;fault(2);}
    if(sched_stage<4){
        need(witness.stage()==1&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==0x32u&&c.mmu.read32(pc)==word);
        if(sched_visits)need(c.inst_count-sched_last==1u);
        sched_last=c.inst_count;need(++sched_visits<=128);
        if(pc==J){need(sched_stage==0&&entries==1&&scheduler_abi(c));sched_stage=1;return;}
        if(pc==J+4u){
            need(sched_stage==1&&entries==4&&c.gpr[3]==initial&&c.mmu.read32(Counter)==initial-1u&&c.lr==pc&&scheduler_abi(c));
            sched_stage=2;return;
        }
        if(pc==J+8u){
            need(!request_switch&&sched_stage==2&&entries==5&&c.lr==pc&&scheduler_abi(c)&&c.mmu.read32(Hint)==0);
            sched_stage=3;return;
        }
        if(pc==J+12u){
            need(sched_stage==3&&entries==5&&c.gpr[3]==Context&&scheduler_abi(c));sched_stage=4;return;
        }
        need(sched_stage==1?((pc>=E&&pc<E+4*enable_words.size())||(pc>=D&&pc<D+4*disable_words.size())||(pc>=R&&pc<R+4*restore_words.size())):
            sched_stage==2&&pc>=S&&pc<S+4*resched_words.size());return;
    }
    need(witness.stage()==1&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u));
    need(!pending&&pc>=L&&pc<L+4*loader_words.size()&&!(pc&3u)&&
         loader_words[(pc-L)/4]==word&&c.mmu.read32(pc)==word);
    need(pc==next_pc||pc==alternate);
    if(visits)need(c.inst_count-last_tick==1);
    else need(pc==L&&entries==6&&outer==1&&c.inst_count-sched_last==1u&&c.gpr[3]==Context);
    last_tick=c.inst_count;need(++visits<=512);
    if(word==0x4c000064u){
        const unsigned gd=gqr_diff(c);unsigned rd=0;
        for(unsigned i=0;i<32;++i)rd+=c.gpr[i]!=gp[i];
        if(corrupt){
            need(rd==1&&c.gpr[14]==(gp[14]^1u)&&!witness.before_rfi(c,pc,word,Other,Mask)&&witness.failure()==2);
            std::cout<<"V737_CONTEXT_REFUSAL integer_corruption=1 witness=2"<<std::endl;std::_Exit(126);
        }
        if(rd||pack_cr(c)!=cr||c.lr!=lr||c.ctr!=ctr||c.xer!=xer||c.srr0!=H||c.srr1!=Prior||gd||c.mmu.read16(Context+0x1a2u)!=0){
            std::cout<<"V737_CONTEXT_MISMATCH gpr="<<rd<<" cr="<<unsigned(pack_cr(c)!=cr)
                     <<" lr="<<unsigned(c.lr!=lr)<<" ctr="<<unsigned(c.ctr!=ctr)<<" xer="<<unsigned(c.xer!=xer)
                     <<" srr0="<<unsigned(c.srr0!=H)<<" srr1="<<unsigned(c.srr1!=Prior)
                     <<" gqr="<<gd<<" exception_state="<<unsigned(c.mmu.read16(Context+0x1a2u)!=0)<<std::endl;
            fault(2);
        }
        need(witness.before_rfi(c,pc,word,Other,Mask));return;
    }
    next_pc=pc+4u;alternate=0;
    const auto op=word>>26;
    if(op==16u||op==18u){
        const uint32_t bits=op==16u?0xfffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
        const uint32_t dst=pc+(((word&bits)^sign)-sign);
        if(op==18u)next_pc=dst;else alternate=dst;
        if(dst<=pc){pending=true;poll_pc=pc;}
    }
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,7> order{J,E,D,R,S,L,H};
    need(c.pc==pc&&entries<order.size());
    if(pc==G){
        need(request_switch&&entries==5&&sched_stage==2&&c.mmu.read32(Counter)==initial-1u);
        std::cout<<"V737_SWITCH_REFUSAL guarded_tail=1 original_switch=0"<<std::endl;std::_Exit(126);
    }
    need(pc==order[entries]&&(pc==H?witness.stage()==4:witness.stage()==1));
    if(pc!=J&&pc!=H)need(live.entry(c,pc,Other,Mask));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(witness.stage()==2||witness.stage()==3){need(live.poll(c,Other,Mask)&&witness.poll(c,Other,Mask));return false;}
    if(witness.stage()==1&&!sched_visits){
        need(c.pc==J&&!(c.msr&0x8000u)&&outer==0);++outer;return false;
    }
    if(request_switch&&sched_stage==2&&entries==5&&c.pc==G&&c.msr==0x32u)return false;
    if(witness.stage()==1&&pending){
        need(live.poll(c,Other,Mask));
        need(c.pc==poll_pc&&c.inst_count==last_tick&&!(c.msr&0x8000u));pending=false;++back_polls;return false;
    }
    fault(3);
}
bool handle_syscall(CPUContext& c){
    need(c.pc==H+4u&&witness.stage()==5&&c.gpr[5]==gp[5]+1u);++stops;c.is_running=false;return true;
}
void interpret_step(CPUContext&){fault(4);}
void micro_interpret(CPUContext&,uint32_t,uint32_t){fault(5);}
void note_null_call(uint32_t,uint32_t){fault(6);}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fault(7);}void GX_WGPIPE_Write16(uint16_t){fault(7);}void GX_WGPIPE_Write32(uint32_t){fault(7);}
void GX_WGPIPE_WriteF32(float){fault(7);}void GX_WGPIPE_WriteF64(double){fault(7);}
uint16_t HW_Reg_Read16(uint32_t){fault(8);}uint32_t HW_Reg_Read32(uint32_t){fault(8);}
void HW_Reg_Write16(uint32_t,uint16_t){fault(8);}void HW_Reg_Write32(uint32_t,uint32_t){fault(8);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt"||mode=="switch");corrupt=mode=="corrupt";request_switch=mode=="switch";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,resume_words);put(L,loader_words);put(J,epilogue_words);put(E,enable_words);put(S,resched_words);put(D,disable_words);put(R,restore_words);put(G,guard_words);
    for(unsigned trial=0;trial<(corrupt||request_switch?1u:8u);++trial){
        witness=ExternalReturnWitness{};live_capture=ExternalReturnWitness{};live=LiveEpilogueWitness({J,E,S,D,R,L,G,Context,CounterDisp,HintDisp,ContextReg,GqrMask});visits=entries=outer=back_polls=sched_visits=sched_stage=0;initial=trial+1u;next_pc=L;alternate=poll_pc=0;pending=false;
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80020000u+trial*0x100u;gp=c.gpr;
        for(unsigned i=0;i<8;++i){
            c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);
            c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);
        }
        cr=pack_cr(c);lr=c.lr=0x80006000u+4u*trial;ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
        c.pc=H;c.msr=Prior;c.srr0=c.srr1=0;c.inst_count=100;c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
        need(witness.capture(c,Other|Mask,Mask)&&live_capture.capture(c,Other|Mask,Mask));
        // Independently construct an exception-state OSContext. The pending
        // interrupt and acknowledgement are fixture state, not game execution.
        for(unsigned i=0;i<0x2c8u;i+=4)c.mmu.write32(Context+i,0);
        for(unsigned i=0;i<32;++i)c.mmu.write32(Context+4*i,gp[i]^(corrupt&&i==14?1u:0u));
        c.mmu.write32(Context+0x80u,cr);c.mmu.write32(Context+0x84u,lr);
        c.mmu.write32(Context+0x88u,ctr);c.mmu.write32(Context+0x8cu,xer);
        c.mmu.write32(Context+0x198u,H);c.mmu.write32(Context+0x19cu,Prior);
        c.mmu.write16(Context+0x1a0u,0);c.mmu.write16(Context+0x1a2u,2);
        for(unsigned i=0;i<8;++i){
            const uint32_t value=0x00040004u+i*0x100u+trial*0x10000u;
            c.mmu.write32(Context+0x1a4u+4*i,value);c.gqr[i]=0;
            gqr[i]=(GqrMask&(1u<<i))?value:0;
        }
        c.mmu.write32(Context-4u,0x12345678u);c.mmu.write32(Context+0x2c8u,0x87654321u);
        // Deliberately wrong live state; the original loader must restore it.
        for(auto& v:c.gpr)v=0xdeadbeefu;
        c.gpr[1]=0x80040000u;c.gpr[2]=0x80025000u;c.gpr[13]=Sda;c.gpr[ContextReg]=Context;scheduler_gp=c.gpr;
        c.mmu.write32(Counter,initial);c.mmu.write32(Hint,request_switch?1u:0u);
        for(auto& f:c.cr){f.lt=false;f.gt=false;f.eq=false;f.so=false;}
        c.lr=0;c.ctr=0;c.xer=0;c.srr0=0x8000b000u;c.srr1=0;c.pc=J;c.msr=0x32u;
        run_game(c);
        need(!corrupt&&!request_switch&&!c.is_running&&witness.stage()==5&&live.stage()==5&&entries==7&&outer==1&&stops==trial+1&&gqr_diff(c)==0);
        need(c.mmu.read32(Context-4u)==0x12345678u&&c.mmu.read32(Context+0x2c8u)==0x87654321u);
    }
    std::cout<<"V762_OWNER_LIVE_EPILOGUE valid=8 original_dispatcher=8 scheduler_enable=8 reschedule=8 native_rfi=8 synthetic_resume=8 fallback=0 continuous_boot=0\n";
}catch(...){fault(9);}
