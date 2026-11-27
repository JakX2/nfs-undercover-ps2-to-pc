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
void refusals(){
    assert(!predict_formatter_branch(0x44000002u,PC,0u,0u,LR));
    assert(!predict_formatter_branch(0u,PC,0u,0u,LR));
    assert(!predict_formatter_branch(b(4),PC+2u,0u,0u,LR));
    assert(!predict_formatter_branch(0x7c000000u,PC,0u,0u,LR));
    assert(!predict_formatter_branch((19u<<26u)|(257u<<1u),PC,0u,0u,LR));
}
}
int main(){
    direct_branches();
    conditional_branches();
    indirect_branches();
    refusals();
    std::cout<<"FORMATTER_BRANCH_DECISION_SOURCE_ONLY direct=1 conditional=1"
                " indirect=1 refusals=1 original_execution=0\n";
}
