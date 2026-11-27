#pragma once
#include "wii_formatter_caller_integer.h"

#include <array>
#include <cstdint>
#include <limits>
#include <optional>

namespace undercover::wii {

// Isolated, source-only witness for a private PPC extsb at the fifth
// callee instruction. This class observes translated code; it never
// executes, emulates, or substitutes the instruction itself.
// The authenticated source and expected output are supplied by the
// owner-private 118..122 symbolic chain.
class FormatterSignextWitness {
public:
    unsigned stage() const { return stage_; }
    bool failed() const { return failed_; }

    template<class C>
    bool arm(C& c,uint32_t root,uint32_t pc,uint32_t instruction,
             uint32_t next_word,uint32_t return_pc,unsigned source_reg,
             uint32_t authenticated_before,uint32_t authenticated_after,
             std::optional<uint32_t> following={},
             std::optional<uint32_t> trailing={},
             std::optional<uint32_t> fourth={},
             std::optional<uint32_t> fifth={},
             std::optional<uint32_t> sixth={}) {
        const unsigned op=instruction>>26u,rs=(instruction>>21u)&31u,
                       ra=(instruction>>16u)&31u,rb=(instruction>>11u)&31u,
                       xo=(instruction>>1u)&1023u;
        if(stage_||failed_||!safe(c)||c.pc!=root||
           root<0x80000000u||root>0x817fffe0u||
           (fourth&&root>0x817fffd8u)||(fifth&&root>0x817fffd4u)||(sixth&&root>0x817fffd0u)||(root&3u)||
           pc!=root+16u||op!=31u||xo!=954u||rb!=0u||
           (instruction&1u)||rs!=ra||rs!=source_reg||
           !(rs==0u||(rs>=3u&&rs<=12u))||
           next_word==0x44000002u||return_pc!=c.lr||
           // The private fixture excludes every slot occupied by the
           // original 118..122 chain and both test-only guards. Do not
           // let a synthetic return alias an earlier instruction slot.
           (trailing&&!following)||(fourth&&!trailing)||(fifth&&!fourth)||(sixth&&!fifth)||
           (following&&*following==0x44000002u)||
           (trailing&&*trailing==0x44000002u)||
           (fourth&&*fourth==0x44000002u)||(fifth&&*fifth==0x44000002u)||(sixth&&*sixth==0x44000002u)||
           (return_pc>=root&&return_pc<=pc+8u+4u*(unsigned(bool(following))+unsigned(bool(trailing))+unsigned(bool(fourth))+unsigned(bool(fifth))+unsigned(bool(sixth))))||
           c.inst_count==std::numeric_limits<uint64_t>::max()||
           !word(c,pc,instruction)||!word(c,pc+4u,next_word)||
           !tail_matches(c,pc,following,trailing,fourth,fifth,sixth)||!word(c,return_pc,0x44000002u))
            return reject();
        const std::array<CallerIntegerInput,1> input{{{rs,authenticated_before}}};
        const auto predicted=predict_caller_integer(instruction,c.gpr,
                                                      pack(c),c.xer,input);
        if(!predicted||!predicted->reg||*predicted->reg!=rs||
           predicted->value!=authenticated_after||
           predicted->cr!=pack(c))return reject();
        cpu_=&c;root_=root;pc_=pc;instruction_=instruction;
        next_word_=next_word;return_pc_=return_pc;
        following_=following;trailing_=trailing;fourth_=fourth;fifth_=fifth;sixth_=sixth;dst_=rs;
        expected_=authenticated_after;gpr_=c.gpr;gqr_=c.gqr;
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
           !tail_matches(c,pc_,following_,trailing_,fourth_,fifth_,sixth_)||
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
    template<class C> static bool word(C& c,uint32_t a,uint32_t expected){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto* first=c.mmu.get_ptr(a);
        auto* last=c.mmu.get_ptr(a+3u);
        return first&&last&&reinterpret_cast<uintptr_t>(last)==
            reinterpret_cast<uintptr_t>(first)+3u&&c.mmu.read32(a)==expected;
    }
    // The fourth optional word is the privately authenticated 126th lookahead
    // when the 125th instruction is the next execution target.
    // The following words are supplied by the already authenticated
    // fixture, never inferred from live guest memory. Every extension
    // moves the terminal guard by precisely one instruction slot.
    template<class C> static bool tail_matches(C& c,uint32_t pc,
        std::optional<uint32_t> following,std::optional<uint32_t> trailing,
        std::optional<uint32_t> fourth,std::optional<uint32_t> fifth,
        std::optional<uint32_t> sixth){
        return word(c,pc+8u,following.value_or(0x44000002u))&&
            (!following||word(c,pc+12u,trailing.value_or(0x44000002u)))&&
            (!trailing||word(c,pc+16u,fourth.value_or(0x44000002u)))&&
            (!fourth||word(c,pc+20u,fifth.value_or(0x44000002u)))&&
            (!fifth||word(c,pc+24u,sixth.value_or(0x44000002u)))&&
            (!sixth||word(c,pc+28u,0x44000002u));
    }
    std::optional<uint32_t> following_{},trailing_{},fourth_{},fifth_{},sixth_{};
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
