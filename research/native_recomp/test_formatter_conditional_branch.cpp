// Synthetic branch labels only. No private game data or native execution.
#include "wii_formatter_conditional_branch.h"
#include <array>
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <iostream>

using namespace undercover::wii;
namespace {
constexpr uint32_t Root=0x80010000u,PC=Root+40u,Ret=Root+0x100u;
constexpr uint32_t Next=0x60000000u,Guard=FormatterConditionalBranchWitness::guard;
constexpr uint32_t bc(unsigned bo,unsigned bi,uint16_t disp,unsigned aa=0u,unsigned lk=0u){
    return (16u<<26u)|(bo<<21u)|(bi<<16u)|
        (uint32_t(disp)&0xfffcu)|(aa?2u:0u)|(lk?1u:0u);
}
struct Mem{
    std::array<uint8_t,512> data{};
    uint8_t* get_ptr(uint32_t at){
        return at>=Root&&at-Root<data.size()?data.data()+(at-Root):nullptr;
    }
    void write32(uint32_t at,uint32_t value){
        for(unsigned i=0;i<4u;++i)*get_ptr(at+i)=uint8_t(value>>(24u-i*8u));
    }
    uint32_t read32(uint32_t at){
        uint32_t out=0;
        for(unsigned i=0;i<4u;++i)out=(out<<8u)|*get_ptr(at+i);
        return out;
    }
};
struct Cpu{
    struct Flag{bool lt=false,gt=false,eq=false,so=false;};
    Mem mmu;
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Flag,8> cr{};
    uint32_t pc=Root,lr=Ret,ctr=0x80010055u,xer=0x80000000u;
    uint32_t msr=0x8032u,srr0=Root,srr1=0x8032u,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
Cpu seed(bool eq,unsigned bo=12u,bool chosen=true){
    Cpu c;
    for(unsigned i=0;i<c.gpr.size();++i)c.gpr[i]=0x12340000u+i;
    c.gqr[4]=0x3f800000u;
    c.cr[0].eq=eq;
    const bool taken=(bo==12u)?eq:!eq;
    const uint32_t target=PC+16u,selected=taken?target:PC+4u;
    const uint32_t unused=taken?PC+4u:target;
    c.mmu.write32(PC,bc(bo,2,16));
    c.mmu.write32(unused,Guard);
    c.mmu.write32(selected,chosen?Next:Guard);
    c.mmu.write32(selected+4u,Guard);
    c.mmu.write32(Ret,Guard);
    return c;
}
void positives(){
    for(const bool eq:{false,true})
    for(const unsigned bo:{4u,12u}){
        Cpu c=seed(eq,bo);
        const bool taken=bo==12u?eq:!eq;
        const uint32_t chosen=taken?PC+16u:PC+4u;
        FormatterConditionalBranchWitness w;
        const auto gpr=c.gpr;const auto count=c.inst_count;
        assert(w.arm(c,Root,PC,bc(bo,2,16),chosen,Next,Ret,80u));
        assert(c.gpr==gpr&&c.inst_count==count&&w.taken()==taken&&w.stage()==1u);
        ++c.inst_count;
        assert(w.observe(c,chosen,Next)&&w.stage()==2u&&!w.failed());
        assert(!w.observe(c,chosen,Next)&&w.failed());
    }
}
void refusal_cases(){
    for(const unsigned fault:{0u,1u,2u,3u,4u,5u,6u,7u,8u,9u,10u}){
        Cpu c=seed(true);
        uint32_t instruction=bc(12,2,16),chosen=PC+16u;
        uint32_t size=80u;
        switch(fault){
        case 0:instruction=bc(16,2,16);break; // CTR-dependent
        case 1:instruction=bc(12,2,16,1u);break; // absolute
        case 2:instruction=bc(12,2,16,0u,1u);break; // LK
        case 3:chosen=PC+4u;break; // false edge
        case 4:c.mmu.write32(PC+4u,Next);break; // unguarded sibling
        case 5:c.mmu.write32(PC+20u,Next);break; // moved stop guard
        case 6:size=48u;break; // outside authentic owner span
        case 7:c.lr^=4u;break; // forged return
        case 8:c.cr[0].eq=false;break; // wrong condition
        case 9:size=60u;break; // selected next guard crosses owner extent
        case 10:
            c.lr=Root+64u;
            c.mmu.write32(c.lr,Guard);
            break; // return alias inside the current owner
        }
        // Authenticate each changed branch encoding before asking whether
        // its *semantics* are admissible, rather than only testing word
        // mismatch against the initially installed branch.
        if(fault<=2u)c.mmu.write32(PC,instruction);
        FormatterConditionalBranchWitness w;
        assert(!w.arm(c,Root,PC,instruction,chosen,Next,Ret,size));
        assert(w.failed()&&w.stage()==0u);
    }
}
void observe_refusals(){
    for(unsigned fault=0;fault<17u;++fault){
        Cpu c=seed(true);
        FormatterConditionalBranchWitness w;
        assert(w.arm(c,Root,PC,bc(12,2,16),PC+16u,Next,Ret,80u));
        ++c.inst_count;
        uint32_t at=PC+16u,word=Next;
        switch(fault){
        case 0:at+=4u;break;
        case 1:word^=1u;break;
        case 2:++c.inst_count;break;
        case 3:c.gpr[9]^=1u;break;
        case 4:c.gqr[4]^=1u;break;
        case 5:c.cr[1].lt=true;break;
        case 6:c.xer^=1u;break;
        case 7:c.lr^=4u;break;
        case 8:c.ctr^=4u;break;
        case 9:c.msr^=1u;break;
        case 10:c.srr0^=4u;break;
        case 11:c.srr1^=4u;break;
        case 12:c.in_callback=true;break;
        case 13:c.mmu.write32(PC+4u,Next);break;
        case 14:c.mmu.write32(PC+20u,Next);break;
        case 15:c.mmu.write32(Ret,Next);break;
        case 16:c.pc+=4u;break;
        }
        assert(!w.observe(c,at,word)&&w.failed()&&w.stage()==1u);
    }
}
}
int main(){
    positives();
    refusal_cases();
    observe_refusals();
    std::cout<<"FORMATTER_CONDITIONAL_BRANCH_SOURCE_ONLY routes=4 arm_refusals=11"
             <<" observe_refusals=17 original_execution=0\n";
}
