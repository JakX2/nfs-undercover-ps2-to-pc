#pragma once
#include "wii_formatter_caller_integer.h"

#include <array>
#include <cstdint>
#include <limits>
#include <span>

namespace undercover::wii {

// A bounded, original-free observer for a straight-line native integer tail.
// The owner fixture must authenticate every code word, operand and result
// before constructing this contract. No guest instruction is executed here.
struct FormatterIntegerTailStep {
    uint32_t word=0;
    std::array<CallerIntegerInput,3> inputs{};
    unsigned input_count=0;
    std::optional<unsigned> destination{};
    uint32_t value=0;
};

class FormatterIntegerTailWitness {
public:
    static constexpr unsigned max_steps=16;
    static constexpr uint32_t guard=0x44000002u;
    unsigned completed()const{return completed_;}
    bool failed()const{return failed_;}
    bool finished()const{return armed_&&!failed_&&completed_==size_;}

    template<class C>bool arm(C& c,uint32_t root,uint32_t first,
        std::span<const FormatterIntegerTailStep> steps,
        uint32_t next_word,uint32_t return_pc){
        if(armed_||failed_||!safe(c)||c.pc!=root||
           root<0x80000000u||root>=0x81800000u||(root&3u)||
           first<root||(first&3u)||steps.empty()||steps.size()>max_steps||
           next_word==guard||c.lr!=return_pc||
           c.inst_count>std::numeric_limits<uint64_t>::max()-steps.size())
            return reject();
        const uint64_t end=uint64_t(first)+4u*steps.size();
        if(end+8u>0x81800000ull||
           (return_pc>=root&&uint64_t(return_pc)<=end+4u)||
           !word(c,uint32_t(end),next_word)||
           !word(c,uint32_t(end)+4u,guard)||!word(c,return_pc,guard))
            return reject();
        // Precompute independent expected snapshots without writing CPU state.
        // No nonvolatile or stack writes are authorized by this observer.
        auto gp=c.gpr;auto cr=pack(c);
        for(unsigned i=0;i<steps.size();++i){
            const auto& s=steps[i];
            if(s.word==guard||s.input_count>s.inputs.size()||
               (!s.destination&&s.value!=0u)||
               !word(c,first+4u*i,s.word))return reject();
            const auto result=predict_caller_integer(s.word,gp,cr,c.xer,
                std::span<const CallerIntegerInput>(s.inputs.data(),s.input_count));
            if(!result||result->reg!=s.destination||
               (result->reg&&result->value!=s.value))return reject();
            if(result->reg)gp[*result->reg]=result->value;
            cr=result->cr;
            words_[i]=s.word;
            expected_[i]={gp,cr};
        }
        root_=root;first_=first;size_=unsigned(steps.size());
        next_=next_word;ret_=return_pc;cpu_=&c;count_=c.inst_count;
        gqr_=c.gqr;xer_=c.xer;ctr_=c.ctr;msr_=c.msr;
        srr0_=c.srr0;srr1_=c.srr1;armed_=true;
        return true;
    }

    // Call once at the next original AOT label, before that label executes.
    // The test/runner must independently enforce the original parent lease.
    template<class C>bool observe(C& c,uint32_t pc,uint32_t instruction){
        if(!armed_||failed_||cpu_!=&c||completed_>=size_||!safe(c)||
           c.pc!=root_||pc!=first_+4u*(completed_+1u)||
           instruction!=(completed_+1u==size_?next_:words_[completed_+1u])||
           c.inst_count!=count_+completed_+1u||
           c.gpr!=expected_[completed_].gp||pack(c)!=expected_[completed_].cr||
           c.gqr!=gqr_||c.xer!=xer_||c.lr!=ret_||c.ctr!=ctr_||c.msr!=msr_||
           c.srr0!=srr0_||c.srr1!=srr1_)return reject();
        for(unsigned i=0;i<size_;++i)
            if(!word(c,first_+4u*i,words_[i]))return reject();
        if(!word(c,first_+4u*size_,next_)||
           !word(c,first_+4u*size_+4u,guard)||!word(c,ret_,guard))
            return reject();
        ++completed_;return true;
    }
private:
    struct Snapshot {std::array<uint32_t,32> gp{};uint32_t cr=0;};
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
    template<class C>static bool word(C& c,uint32_t a,uint32_t expected){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==
            reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==expected;
    }
    const void* cpu_=nullptr;
    std::array<uint32_t,max_steps> words_{};
    std::array<Snapshot,max_steps> expected_{};
    std::array<uint32_t,8> gqr_{};
    uint32_t root_=0,first_=0,next_=0,ret_=0,xer_=0,ctr_=0,msr_=0,srr0_=0,srr1_=0;
    uint64_t count_=0;
    unsigned size_=0,completed_=0;
    bool armed_=false,failed_=false;
};
} // namespace undercover::wii
