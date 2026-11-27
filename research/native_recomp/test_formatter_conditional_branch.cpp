// Synthetic branch labels only. No private game data or native execution.
#include "wii_formatter_conditional_branch.h"
#include "wii_formatter_report_sixth_immediate.h"
#include <optional>
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
        c.pc=chosen; // generated cross-root dispatch assigns ctx.pc
        assert(w.observe(c,chosen,Next)&&w.stage()==2u&&!w.failed());
        assert(!w.observe(c,chosen,Next)&&w.failed());
    }
}
void condition_register_matrix(){
    // Exercise every CR field/bit and both true/false branch outcomes.
    // These are synthetic label transitions, not executed PPC instructions.
    for(unsigned bi=0u;bi<32u;++bi)
    for(const unsigned bo:{4u,12u})
    for(const bool set:{false,true}){
        Cpu c=seed(set,bo);
        c.cr[0].eq=false;
        auto& f=c.cr[bi/4u];
        switch(bi%4u){
        case 0u:f.lt=set;break;
        case 1u:f.gt=set;break;
        case 2u:f.eq=set;break;
        case 3u:f.so=set;break;
        default:assert(false);
        }
        const uint32_t instruction=bc(bo,bi,16);
        const bool taken=bo==12u?set:!set;
        const uint32_t selected=taken?PC+16u:PC+4u;
        c.mmu.write32(PC,instruction);
        FormatterConditionalBranchWitness witness;
        assert(witness.arm(c,Root,PC,instruction,selected,Next,Ret,80u));
        assert(witness.taken()==taken&&witness.stage()==1u);
        ++c.inst_count;
        c.pc=selected;
        assert(witness.observe(c,selected,Next)&&witness.stage()==2u);
    }
}
// Join a synthetic original-127 addi to both outcomes of original-128 bc.
// The register update and branch transition are manually applied test state.
void chained_sixth_immediate_branch(){
    const uint32_t li=(14u<<26u)|(6u<<21u)|0x8000u;
    for(const bool eq:{false,true})
    for(const unsigned bo:{4u,12u}){
        Cpu c=seed(eq,bo);
        const uint32_t branch=bc(bo,2u,16u);
        const bool taken=bo==12u?eq:!eq;
        const uint32_t selected=taken?PC+16u:PC+4u;
        c.mmu.write32(PC-4u,li);
        const std::optional<uint32_t> following=
            taken?std::nullopt:std::optional<uint32_t>{Next};
        FormatterSixthImmediateWitness previous;
        assert(previous.arm(c,Root,PC-4u,li,branch,Ret,6u,
                            0xffff8000u,following));
        c.gpr[6u]=0xffff8000u;
        ++c.inst_count;
        assert(previous.observe(c,PC,branch));
        assert(previous.stage()==2u&&!previous.failed());
        FormatterConditionalBranchWitness branch_edge;
        assert(branch_edge.arm(c,Root,PC,branch,selected,Next,Ret,80u));
        ++c.inst_count;
        c.pc=selected;
        assert(branch_edge.observe(c,selected,Next));
        assert(branch_edge.stage()==2u&&!branch_edge.failed());
    }
    {
        Cpu c=seed(false,12u);
        const uint32_t branch=bc(12u,2u,16u);
        c.mmu.write32(PC-4u,li);
        FormatterSixthImmediateWitness missing;
        assert(!missing.arm(c,Root,PC-4u,li,branch,Ret,6u,
                            0xffff8000u));
        FormatterSixthImmediateWitness wrong;
        assert(!wrong.arm(c,Root,PC-4u,li,branch,Ret,6u,
                          0xffff8000u,branch));
        FormatterSixthImmediateWitness correct;
        assert(correct.arm(c,Root,PC-4u,li,branch,Ret,6u,
                           0xffff8000u,Next));
        c.mmu.write32(PC+8u,Next);
        c.gpr[6u]=0xffff8000u;
        ++c.inst_count;
        assert(!correct.observe(c,PC,branch)&&correct.failed());
    }
    {
        Cpu c=seed(true,12u);
        const uint32_t branch=bc(12u,2u,16u);
        c.mmu.write32(PC-4u,li);
        FormatterSixthImmediateWitness extra;
        assert(!extra.arm(c,Root,PC-4u,li,branch,Ret,6u,
                          0xffff8000u,Next));
    }
}
void refusal_cases(){
    for(const unsigned fault:{0u,1u,2u,3u,4u,5u,6u,7u,8u,9u,10u,11u}){
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
        case 11:
            instruction=bc(12,2,static_cast<uint16_t>(-16));
            chosen=PC-16u;
            c.mmu.write32(chosen,Next);
            c.mmu.write32(chosen+4u,Guard);
            break; // backward branch must not overwrite proven prefix
        }
        // Authenticate each changed branch encoding before asking whether
        // its *semantics* are admissible, rather than only testing word
        // mismatch against the initially installed branch.
        if(fault<=2u||fault==11u)c.mmu.write32(PC,instruction);
        FormatterConditionalBranchWitness w;
        assert(!w.arm(c,Root,PC,instruction,chosen,Next,Ret,size));
        assert(w.failed()&&w.stage()==0u);
    }
}
void observe_refuses_old_root_without_native_dispatch(){
    Cpu c=seed(true);
    FormatterConditionalBranchWitness witness;
    assert(witness.arm(c,Root,PC,bc(12u,2u,16u),
                       PC+16u,Next,Ret,80u));
    ++c.inst_count;
    // A caller continuing with the old root does not prove that the
    // selected target root was actually dispatched.
    assert(!witness.observe(c,PC+16u,Next));
    assert(witness.failed()&&witness.stage()==1u);
}
void observe_refusals(){
    for(unsigned fault=0;fault<22u;++fault){
        Cpu c=seed(true);
        FormatterConditionalBranchWitness w;
        assert(w.arm(c,Root,PC,bc(12,2,16),PC+16u,Next,Ret,80u));
        ++c.inst_count;
        c.pc=PC+16u; // correct AOT target-root context for every refusal
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
        case 17:c.mmu.write32(PC,bc(12u,3u,16));break;
        case 18:c.mmu.write32(PC+16u,bc(20u,0u,4));break;
        case 19:c.is_running=false;break;
        case 20:c.dispatch_saved_ctx=1u;break;
        case 21:c.mmu.write32(PC+4u,bc(20u,0u,4));break;
        }
        assert(!w.observe(c,at,word)&&w.failed()&&w.stage()==1u);
    }
}
}
int main(){
    positives();
    condition_register_matrix();
    chained_sixth_immediate_branch();
    refusal_cases();
    observe_refuses_old_root_without_native_dispatch();
    observe_refusals();
    std::cout<<"FORMATTER_CONDITIONAL_BRANCH_SOURCE_ONLY routes=4 cr_matrix=128 chained_127_128=4 cross_root=1 arm_refusals=12"
             <<" observe_refusals=22 original_execution=0\n";
}
