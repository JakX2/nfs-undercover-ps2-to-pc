// Only synthetic PPC words; no original game code or execution.
#include "wii_formatter_branch_decision.h"
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <iostream>

using namespace undercover::wii;
namespace {
constexpr uint32_t PC=0x80010028u, LR=0x800101f3u, EQ=0x20000000u;
constexpr uint32_t b(int32_t disp,bool aa=false,bool lk=false){
    return (18u<<26u)|(uint32_t(disp)&0x03fffffcu)|
        (aa?2u:0u)|(lk?1u:0u);
}
constexpr uint32_t bc(unsigned bo,unsigned bi,int16_t disp,bool aa=false,bool lk=false){
    return (16u<<26u)|(bo<<21u)|(bi<<16u)|
        (uint32_t(uint16_t(disp))&0xfffcu)|
        (aa?2u:0u)|(lk?1u:0u);
}
void direct_branches(){
    auto f=predict_formatter_branch(b(12),PC,0u,42u,LR);
    assert(f&&f->taken&&f->next_pc==PC+12u&&f->target==PC+12u);
    assert(f->ctr==42u&&f->lr==LR&&!f->linked&&!f->cr_tested);
    f=predict_formatter_branch(b(-8),PC,0u,42u,LR);
    assert(f&&f->target==PC-8u&&f->next_pc==PC-8u);
    f=predict_formatter_branch(b(0x20,true,true),PC,0u,42u,LR);
    assert(f&&f->absolute&&f->linked&&f->target==0x20u&&f->lr==PC+4u);
    f=predict_formatter_branch(b(-4,true),PC,0u,42u,LR);
    assert(f&&f->target==0xfffffffcu);
}
void conditional_branches(){
    auto f=predict_formatter_branch(bc(12,2,16),PC,EQ,9u,LR);
    assert(f&&f->taken&&f->next_pc==PC+16u&&f->cr_tested&&!f->ctr_decremented);
    f=predict_formatter_branch(bc(12,2,16),PC,0u,9u,LR);
    assert(f&&!f->taken&&f->next_pc==PC+4u&&f->ctr==9u);
    f=predict_formatter_branch(bc(4,2,16),PC,0u,9u,LR);
    assert(f&&f->taken);
    f=predict_formatter_branch(bc(4,2,16),PC,EQ,9u,LR);
    assert(f&&!f->taken);
    f=predict_formatter_branch(bc(16,0,16),PC,EQ,2u,LR);
    assert(f&&f->taken&&f->ctr==1u&&f->ctr_decremented&&!f->cr_tested);
    f=predict_formatter_branch(bc(16,0,16),PC,EQ,1u,LR);
    assert(f&&!f->taken&&f->ctr==0u);
    f=predict_formatter_branch(bc(18,0,16),PC,0u,1u,LR);
    assert(f&&f->taken&&f->ctr==0u);
    f=predict_formatter_branch(bc(16,0,16),PC,0u,0u,LR);
    assert(f&&f->taken&&f->ctr==0xffffffffu);
    f=predict_formatter_branch(bc(12,2,16,false,true),PC,0u,9u,LR);
    assert(f&&!f->taken&&f->lr==PC+4u);
    f=predict_formatter_branch(bc(12,2,-16),PC,EQ,9u,LR);
    assert(f&&f->next_pc==PC-16u);
}
void indirect_branches(){
    auto f=predict_formatter_branch(0x4e800020u,PC,0u,0x80010203u,LR);
    assert(f&&f->taken&&f->target==(LR&~3u)&&f->lr==LR);
    assert(f->kind==FormatterBranchPrediction::Kind::LinkRegister);
    f=predict_formatter_branch(0x4e800021u,PC,0u,0x80010203u,LR);
    assert(f&&f->taken&&f->target==(LR&~3u)&&f->lr==PC+4u);
    f=predict_formatter_branch(0x4e800420u,PC,0u,0x80010203u,LR);
    assert(f&&f->target==0x80010200u&&f->ctr==0x80010203u);
    assert(f->kind==FormatterBranchPrediction::Kind::CountRegister);
    f=predict_formatter_branch(0x4e800421u,PC,0u,0x80010203u,LR);
    assert(f&&f->target==0x80010200u&&f->lr==PC+4u);
    assert(!predict_formatter_branch((19u<<26u)|(16u<<21u)|(528u<<1u),
                                     PC,0u,2u,LR));
}
void exhaustive_branch_conditions(){
    // Bit index BI is architecturally big-endian in the 32-bit CR.
    // Test every CR bit position rather than only CR0.EQ.
    for(unsigned bi=0u;bi<32u;++bi){
        const uint32_t bit=uint32_t(1u)<<(31u-bi);
        for(unsigned present=0u;present<2u;++present){
            const uint32_t cr=present?bit:~bit;
            const auto eq=predict_formatter_branch(
                bc(12u,bi,16),PC,cr,8u,LR);
            const auto ne=predict_formatter_branch(
                bc(4u,bi,-16),PC,cr,8u,LR);
            assert(eq&&ne&&eq->cr_tested&&ne->cr_tested);
            assert(eq->taken==bool(present));
            assert(ne->taken!=bool(present));
            assert(eq->next_pc==(present?PC+16u:PC+4u));
            assert(ne->next_pc==(present?PC+4u:PC-16u));
            assert(eq->ctr==8u&&ne->ctr==8u);
            assert(eq->lr==LR&&ne->lr==LR);
        }
    }
    for(uint32_t ctr:{0u,1u,2u,0xffffffffu}){
        const auto decrement_nonzero=predict_formatter_branch(
            bc(16u,0u,16),PC,0u,ctr,LR);
        const auto decrement_zero=predict_formatter_branch(
            bc(18u,0u,16),PC,0u,ctr,LR);
        assert(decrement_nonzero&&decrement_zero);
        assert(decrement_nonzero->ctr==ctr-1u);
        assert(decrement_zero->ctr==ctr-1u);
        assert(decrement_nonzero->taken==bool(ctr-1u));
        assert(decrement_zero->taken!=bool(ctr-1u));
    }
    // Both ends of the PPC signed displacement ranges must be exact.
    auto edge=predict_formatter_branch(b(0x1fffffcu),PC,0u,0u,LR);
    assert(edge&&edge->target==PC+0x1fffffcu);
    edge=predict_formatter_branch(b(-0x2000000),PC,0u,0u,LR);
    assert(edge&&edge->target==PC-0x2000000u);
    edge=predict_formatter_branch(bc(20u,0u,32764),PC,0u,0u,LR);
    assert(edge&&edge->target==PC+32764u);
    edge=predict_formatter_branch(bc(20u,0u,-32768),PC,0u,0u,LR);
    assert(edge&&edge->target==PC-32768u);
    // LK updates LR even on an untaken conditional branch, while the
    // old LR remains the bclrl target.
    auto link=predict_formatter_branch(
        bc(12u,2u,8,false,true),PC,0u,4u,LR);
    assert(link&&!link->taken&&link->lr==PC+4u);
    link=predict_formatter_branch(0x4e800021u,PC,0u,4u,LR);
    assert(link&&link->taken&&link->target==(LR&~3u)&&link->lr==PC+4u);
    // BH=11 is a valid hint for either kind of indirect branch.
    for(uint32_t base:{0x4e800020u,0x4e800420u}){
        auto hinted=predict_formatter_branch(base|0x1800u,PC,0u,4u,LR);
        assert(hinted&&hinted->taken);
    }
}
void refusals(){
    assert(!predict_formatter_branch(0x44000002u,PC,0u,0u,LR));
    assert(!predict_formatter_branch(0u,PC,0u,0u,LR));
    assert(!predict_formatter_branch(b(4),PC+2u,0u,0u,LR));
    assert(!predict_formatter_branch(0x7c000000u,PC,0u,0u,LR));
    assert(!predict_formatter_branch((19u<<26u)|(257u<<1u),PC,0u,0u,LR));
    // Reserved XL bits 16..18 and BH hints 01/10 must fail closed
    // even if the remaining word otherwise names bclr/bcctr.
    for(uint32_t base:{0x4e800020u,0x4e800420u}){
        for(uint32_t reserved:{0x2000u,0x4000u,0x8000u}){
            assert(!predict_formatter_branch(
                base|reserved,PC,0u,0x80010203u,LR));
        }
        for(uint32_t bh:{0x0800u,0x1000u}){
            assert(!predict_formatter_branch(
                base|bh,PC,0u,0x80010203u,LR));
        }
    }
}
}
int main(){
    direct_branches();
    conditional_branches();
    exhaustive_branch_conditions();
    indirect_branches();
    refusals();
    std::cout<<"FORMATTER_BRANCH_DECISION_SOURCE_ONLY direct=1 conditional=1"
                " indirect=1 refusals=1 original_execution=0\n";
}
