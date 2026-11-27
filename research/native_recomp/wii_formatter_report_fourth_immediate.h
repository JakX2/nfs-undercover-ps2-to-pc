#pragma once
#include "wii_formatter_caller_integer.h"

#include <array>
#include <cstdint>
#include <limits>

namespace undercover::wii {

// Source-only witness for one native PowerPC addi rD,r0,SIMM following
// the authenticated 124th instruction. The witness only observes genuine
// NWiiRecomp-generated execution. It does not interpret guest instructions.
class FormatterFourthImmediateWitness {
public:
    unsigned stage() const { return stage_; }
    bool failed() const { return failed_; }

    template<class C>
    bool arm(C& c,uint32_t root,uint32_t pc,uint32_t instruction,
             uint32_t next_word,uint32_t return_pc,unsigned dst,
             uint32_t authenticated_result) {
        const unsigned op=instruction>>26u,rt=(instruction>>21u)&31u,
                       ra=(instruction>>16u)&31u;
        if(stage_||failed_||!safe(c)||c.pc!=root||
           root<0x80000000u||root>0x817fffd8u||(root&3u)||
           pc!=root+28u||op!=14u||ra!=0u||rt!=dst||
           !(dst==0u||(dst>=3u&&dst<=12u))||
           next_word==0x44000002u||return_pc!=c.lr||
           (return_pc>=root&&return_pc<=pc+8u)||
           c.inst_count==std::numeric_limits<uint64_t>::max()||
           !word(c,pc,instruction)||!word(c,pc+4u,next_word)||
           !word(c,pc+8u,0x44000002u)||
           !word(c,return_pc,0x44000002u))
            return reject();
        // PPC RA=0 means literal zero, not the current contents of GPR0.
        // The predictor deliberately has zero live register inputs.
        const auto predicted=predict_caller_zero_input_addi(
            instruction,c.gpr,pack(c),c.xer);
        if(!predicted||!predicted->reg||*predicted->reg!=dst||
           predicted->value!=authenticated_result||
           predicted->cr!=pack(c))return reject();
        cpu_=&c;root_=root;pc_=pc;instruction_=instruction;
        next_word_=next_word;return_pc_=return_pc;dst_=dst;
        expected_=authenticated_result;gpr_=c.gpr;gqr_=c.gqr;
        cr_=pack(c);xer_=c.xer;lr_=c.lr;ctr_=c.ctr;
        msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;
        count_=c.inst_count;stage_=1u;
        return true;
    }

    template<class C>
    bool observe(C& c,uint32_t stop_pc,uint32_t stop_word) {
        if(stage_!=1u||failed_||cpu_!=&c||!safe(c)||c.pc!=root_||
           stop_pc!=pc_+4u||stop_word!=next_word_||
           c.inst_count!=count_+1u||pack(c)!=cr_||c.xer!=xer_||
           c.gqr!=gqr_||c.lr!=lr_||c.ctr!=ctr_||c.msr!=msr_||
           c.srr0!=srr0_||c.srr1!=srr1_||
           !word(c,pc_,instruction_)||!word(c,pc_+4u,next_word_)||
           !word(c,pc_+8u,0x44000002u)||
           !word(c,return_pc_,0x44000002u))
            return reject();
        for(unsigned r=0;r<32u;++r)
            if(c.gpr[r]!=(r==dst_?expected_:gpr_[r]))
                return reject();
        stage_=2u;
        return true;
    }

private:
    bool reject(){failed_=true;return false;}
    template<class C> static bool safe(C& c){
        return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;
    }
    template<class C> static uint32_t pack(C& c){
        uint32_t out=0;
        for(const auto& f:c.cr)
            out=(out<<4u)|(unsigned(f.lt)<<3u)|(unsigned(f.gt)<<2u)|
                (unsigned(f.eq)<<1u)|unsigned(f.so);
        return out;
    }
    template<class C> static bool word(C& c,uint32_t address,uint32_t expected){
        if((address&3u)||address<0x80000000u||address>0x817ffffcu)
            return false;
        auto* first=c.mmu.get_ptr(address);
        auto* last=c.mmu.get_ptr(address+3u);
        return first&&last&&reinterpret_cast<uintptr_t>(last)==
            reinterpret_cast<uintptr_t>(first)+3u&&
            c.mmu.read32(address)==expected;
    }
    const void* cpu_=nullptr;
    std::array<uint32_t,32> gpr_{};
    std::array<uint32_t,8> gqr_{};
    uint32_t root_=0,pc_=0,instruction_=0,next_word_=0,return_pc_=0;
    uint32_t expected_=0,cr_=0,xer_=0,lr_=0,ctr_=0,msr_=0,srr0_=0,srr1_=0;
    uint64_t count_=0;
    unsigned dst_=0,stage_=0;
    bool failed_=false;
};

} // namespace undercover::wii
