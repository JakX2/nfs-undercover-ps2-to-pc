#pragma once
#include "wii_formatter_branch_decision.h"
#include <array>
#include <cstdint>
#include <limits>

namespace undercover::wii {

// Source-only witness for a privately authenticated original-128 bc branch.
// It observes a real AOT label transition; neither arm nor observe advances
// guest PC or interprets a guest instruction. The parent frame/branch fixture
// remains a separate required gate, not evidence supplied by this class.
class FormatterConditionalBranchWitness {
public:
    static constexpr uint32_t guard=0x44000002u;
    unsigned stage()const{return stage_;}
    bool failed()const{return failed_;}
    bool taken()const{return taken_;}

    template<class C>bool arm(C& c,uint32_t root,uint32_t pc,
        uint32_t instruction,uint32_t selected_pc,uint32_t selected_word,
        uint32_t return_pc,uint32_t owner_size){
        if(stage_||failed_||!safe(c)||c.pc!=root||
           root<0x80000000u||root>0x817fff90u||(root&3u)||
           pc!=root+40u||owner_size<48u||owner_size>65536u||
           (owner_size&3u)||uint64_t(root)+owner_size>0x81800000ull||
           c.inst_count==std::numeric_limits<uint64_t>::max()||
           selected_word==guard||c.lr!=return_pc||
           !word(c,pc,instruction)||!word(c,return_pc,guard))
            return reject();
        const auto predicted=predict_formatter_branch(
            instruction,pc,pack(c),c.ctr,c.lr);
        if(!predicted||
           predicted->kind!=FormatterBranchPrediction::Kind::Conditional||
           !predicted->cr_tested||predicted->ctr_decremented||
           predicted->linked||predicted->absolute||
           predicted->ctr!=c.ctr||predicted->lr!=c.lr||
           // This witness cannot rewrite already authenticated 118-127
           // prefix words or branch to its own/fallthrough instruction.
           // Forward, non-adjacent local targets only.
           uint64_t(predicted->target)<=uint64_t(pc)+4u||
           predicted->next_pc!=selected_pc)return reject();
        const auto in_owner=[&](uint32_t at){
            return !(at&3u)&&at>=root&&
                uint64_t(at)+4u<=uint64_t(root)+owner_size;
        };
        const uint32_t unused=predicted->taken?pc+4u:predicted->target;
        if(!in_owner(pc)||!in_owner(selected_pc)||!in_owner(selected_pc+4u)||
           !in_owner(unused)||selected_pc==unused||selected_pc==pc||
           in_owner(return_pc)||return_pc==selected_pc||return_pc==unused||
           !word(c,selected_pc,selected_word)||!word(c,unused,guard)||
           !word(c,selected_pc+4u,guard))return reject();
        cpu_=&c;root_=root;pc_=pc;instruction_=instruction;
        selected_pc_=selected_pc;selected_word_=selected_word;
        unused_pc_=unused;return_pc_=return_pc;taken_=predicted->taken;
        gpr_=c.gpr;gqr_=c.gqr;cr_=pack(c);xer_=c.xer;
        lr_=c.lr;ctr_=c.ctr;msr_=c.msr;
        srr0_=c.srr0;srr1_=c.srr1;count_=c.inst_count;
        stage_=1u;return true;
    }

    template<class C>bool observe(C& c,uint32_t arrival_pc,uint32_t arrival_word){
        if(stage_!=1u||failed_||cpu_!=&c||!safe(c)||c.pc!=root_||
           arrival_pc!=selected_pc_||arrival_word!=selected_word_||
           c.inst_count!=count_+1u||c.gpr!=gpr_||c.gqr!=gqr_||
           pack(c)!=cr_||c.xer!=xer_||c.lr!=lr_||c.ctr!=ctr_||
           c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_||
           !word(c,pc_,instruction_)||
           !word(c,selected_pc_,selected_word_)||
           !word(c,unused_pc_,guard)||
           !word(c,selected_pc_+4u,guard)||
           !word(c,return_pc_,guard))return reject();
        stage_=2u;return true;
    }
private:
    bool reject(){failed_=true;return false;}
    template<class C>static bool safe(C& c){
        return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;
    }
    template<class C>static uint32_t pack(C& c){
        uint32_t out=0;
        for(const auto& f:c.cr)
            out=(out<<4u)|(unsigned(f.lt)<<3u)|(unsigned(f.gt)<<2u)|
                (unsigned(f.eq)<<1u)|unsigned(f.so);
        return out;
    }
    template<class C>static bool word(C& c,uint32_t at,uint32_t expected){
        if((at&3u)||at<0x80000000u||at>0x817ffffcu)return false;
        auto* p=c.mmu.get_ptr(at),*q=c.mmu.get_ptr(at+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==
            reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(at)==expected;
    }
    const void* cpu_=nullptr;
    std::array<uint32_t,32> gpr_{};
    std::array<uint32_t,8> gqr_{};
    uint32_t root_=0,pc_=0,instruction_=0,selected_pc_=0;
    uint32_t selected_word_=0,unused_pc_=0,return_pc_=0;
    uint32_t cr_=0,xer_=0,lr_=0,ctr_=0,msr_=0,srr0_=0,srr1_=0;
    uint64_t count_=0;
    unsigned stage_=0;
    bool taken_=false,failed_=false;
};
} // namespace undercover::wii
