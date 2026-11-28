#pragma once
#include "wii_formatter_caller_integer.h"
#include <array>
#include <cstdint>
#include <limits>

namespace undercover::wii {

// Read-only witness for a signed immediate comparison at the independently
// dispatched target of original 128. The translated comparison executes
// between these two hooks. This class never writes guest CPU state or PC.
class FormatterCompare129Witness {
public:
    static constexpr uint32_t guard=0x44000002u;
    unsigned stage()const{return stage_;}
    bool failed()const{return failed_;}

    template<class C>bool arm(C& c,uint32_t root,uint32_t comparison,
        uint32_t next_pc,uint32_t next_word,uint32_t return_pc,
        CallerIntegerInput input,bool previous_branch_verified){
        if(stage_||failed_||!previous_branch_verified||!safe(c)||
           c.pc!=root||root<0x80000000u||root>0x817ffff4u||(root&3u)||
           next_pc!=root+4u||comparison>>26u!=11u||
           (comparison&0x00600000u)||input.reg>=32u||
           ((comparison>>16u)&31u)!=input.reg||
           next_word==guard||c.lr!=return_pc||
           (return_pc>=root&&return_pc<=root+8u)||
           c.inst_count==std::numeric_limits<uint64_t>::max()||
           !word(c,root,comparison)||!word(c,next_pc,next_word)||
           !word(c,root+8u,guard)||!word(c,return_pc,guard))
            return reject();
        const std::array<CallerIntegerInput,1> operands{{input}};
        const auto expected=predict_caller_integer(
            comparison,c.gpr,pack(c),c.xer,operands);
        if(!expected||expected->reg)return reject();

        cpu_=&c;root_=root;comparison_=comparison;next_word_=next_word;
        return_pc_=return_pc;gpr_=c.gpr;gqr_=c.gqr;cr_=expected->cr;
        xer_=c.xer;lr_=c.lr;ctr_=c.ctr;msr_=c.msr;
        srr0_=c.srr0;srr1_=c.srr1;count_=c.inst_count;stage_=1u;
        return true;
    }

    // The compare and its sequential successor are in the same native
    // target root. The generated label hook carries the precise next PC,
    // while CPUContext::pc retains the selected root's dispatch PC.
    template<class C>bool observe(C& c,uint32_t label,uint32_t instruction){
        if(stage_!=1u||failed_||cpu_!=&c||!safe(c)||c.pc!=root_||
           label!=root_+4u||instruction!=next_word_||
           c.inst_count!=count_+1u||c.gpr!=gpr_||c.gqr!=gqr_||
           pack(c)!=cr_||c.xer!=xer_||c.lr!=lr_||c.ctr!=ctr_||
           c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_||
           !word(c,root_,comparison_)||!word(c,label,next_word_)||
           !word(c,root_+8u,guard)||!word(c,return_pc_,guard))
            return reject();
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
    uint32_t root_=0,comparison_=0,next_word_=0,return_pc_=0;
    uint32_t cr_=0,xer_=0,lr_=0,ctr_=0,msr_=0,srr0_=0,srr1_=0;
    uint64_t count_=0;
    unsigned stage_=0;
    bool failed_=false;
};

} // namespace undercover::wii
