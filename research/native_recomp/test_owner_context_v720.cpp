#include "runtime/cpu_context.h"
#include "wii_external_return_v706.h"
#include "rfi_test_v708.h"
#include "owner_context_input.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using namespace undercover::wii;
using nwii::runtime::CPUContext;
constexpr uint32_t Context=0x80010000u,Other=0x100u,Mask=8u,Prior=0x8032u;
static ExternalReturnWitness witness;
static std::array<uint32_t,32> gp;
static std::array<uint32_t,8> gqr;
static uint32_t cr=0,lr=0,ctr=0,xer=0;
static uint32_t next_pc=0,alternate=0,poll_pc=0;
static uint64_t last_tick=0;
static unsigned visits=0,entries=0,outer=0,back_polls=0,stops=0;
static bool pending=false,corrupt=false;
[[noreturn]]static void fault(unsigned kind,unsigned line=0){
    std::cout<<"V720_CONTEXT_FAULT kind="<<kind<<" line="<<line<<" stage="<<witness.stage()
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
        need(!pending&&entries==2&&witness.resume(c,pc,word,Other,Mask));
        need(gqr_diff(c)==0&&c.mmu.read16(Context+0x1a2u)==0);
        return;
    }
    need(witness.stage()==1&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u));
    need(!pending&&pc>=L&&pc<L+4*loader_words.size()&&!(pc&3u)&&
         loader_words[(pc-L)/4]==word&&c.mmu.read32(pc)==word);
    need(pc==next_pc||pc==alternate);
    if(visits)need(c.inst_count-last_tick==1);
    else need(pc==L&&entries==1&&outer==1);
    last_tick=c.inst_count;need(++visits<=512);
    if(word==0x4c000064u){
        const unsigned gd=gqr_diff(c);unsigned rd=0;
        for(unsigned i=0;i<32;++i)rd+=c.gpr[i]!=gp[i];
        if(corrupt){
            need(rd==1&&c.gpr[14]==(gp[14]^1u)&&!witness.before_rfi(c,pc,word,Other,Mask)&&witness.failure()==2);
            std::cout<<"V720_CONTEXT_REFUSAL integer_corruption=1 witness=2"<<std::endl;std::_Exit(126);
        }
        if(rd||pack_cr(c)!=cr||c.lr!=lr||c.ctr!=ctr||c.xer!=xer||c.srr0!=H||c.srr1!=Prior||gd||c.mmu.read16(Context+0x1a2u)!=0){
            std::cout<<"V720_CONTEXT_MISMATCH gpr="<<rd<<" cr="<<unsigned(pack_cr(c)!=cr)
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
    need(c.pc==pc&&((entries==0&&pc==L&&witness.stage()==1)||(entries==1&&pc==H&&witness.stage()==4)));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(witness.stage()==2||witness.stage()==3){need(witness.poll(c,Other,Mask));return false;}
    if(witness.stage()==1&&!visits){
        need(c.pc==L&&!(c.msr&0x8000u)&&outer==0);++outer;return false;
    }
    if(witness.stage()==1&&pending){
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
    need(argc==2);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt");corrupt=mode=="corrupt";
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,resume_words);put(L,loader_words);
    for(unsigned trial=0;trial<(corrupt?1u:8u);++trial){
        witness=ExternalReturnWitness{};visits=entries=outer=back_polls=0;next_pc=L;alternate=poll_pc=0;pending=false;
        for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
        c.gpr[1]=0x80020000u+trial*0x100u;gp=c.gpr;
        for(unsigned i=0;i<8;++i){
            c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);
            c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);
        }
        cr=pack_cr(c);lr=c.lr=0x80006000u+4u*trial;ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
        c.pc=H;c.msr=Prior;c.srr0=c.srr1=0;c.inst_count=100;c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
        need(witness.capture(c,Other|Mask,Mask));
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
        c.gpr[3]=Context;c.gpr[1]=0x80030000u;
        for(auto& f:c.cr){f.lt=false;f.gt=false;f.eq=false;f.so=false;}
        c.lr=0;c.ctr=0;c.xer=0;c.srr0=0x8000b000u;c.srr1=0;c.pc=L;c.msr=0x32u;
        run_game(c);
        need(!corrupt&&!c.is_running&&witness.stage()==5&&entries==2&&outer==1&&stops==trial+1&&gqr_diff(c)==0);
        need(c.mmu.read32(Context-4u)==0x12345678u&&c.mmu.read32(Context+0x2c8u)==0x87654321u);
    }
    std::cout<<"V720_OWNER_CONTEXT_AOT valid=8 original_loader=1 native_rfi=8 synthetic_resume=8 integer_context=8 fallback=0 continuous_boot=0\n";
}catch(...){fault(9);}
