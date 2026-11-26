#pragma once
#include "wii_cooperative_context_v1306.h"
#include <span>

namespace undercover::wii {
// A private authenticated linear save leaf plus its original caller label.
// Hooks observe native instructions, never execute the save or write RAM.
class CooperativeSaveLane {
public:
    struct Expectation {
        CooperativeContextWitness::Geometry geometry;
        std::span<const uint32_t> words;
        uint32_t return_word;
        unsigned gqr_mask;
    };
    explicit CooperativeSaveLane(Expectation e):e_(e),context_(e.geometry){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned abi_failure()const{return context_.failure();}
    unsigned visits()const{return visits_;}
    const CooperativeContextWitness& context()const{return context_;}
    template<class C>bool capture(C& c,bool held){
        if(stage_||error_||e_.words.empty()||e_.words.size()>128u||e_.words.back()!=0x4e800020u||
           !e_.gqr_mask||e_.gqr_mask>255u||!word(c,e_.geometry.save_return,e_.return_word))return fail(1);
        for(unsigned i=0;i<e_.words.size();++i)if(!word(c,e_.geometry.save+4u*i,e_.words[i]))return fail(1);
        if(!context_.capture(c,held))return fail(2);
        cpu_=&c;last_=c.inst_count;gqr_=c.gqr;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||error_||cpu_!=&c||!held||!c.is_running||c.in_callback||
           c.dispatch_saved_ctx||c.inst_count-last_!=1u||c.gqr!=gqr_)return fail(3);
        last_=c.inst_count;
        if(visits_==e_.words.size()){
            if(pc!=e_.geometry.save_return||w!=e_.return_word||!word(c,pc,w)||!context_.saved(c,held))return fail(4);
            for(unsigned i=0;i<8u;++i)if((e_.gqr_mask&(1u<<i))&&
                !word(c,e_.geometry.context+0x1a4u+4u*i,gqr_[i]))return fail(5);
            stage_=2;return true;
        }
        if(pc!=e_.geometry.save+4u*visits_||w!=e_.words[visits_]||!word(c,pc,w))return fail(3);
        ++visits_;return true;
    }
    template<class C>bool preserved(C& c,bool held)const{
        return stage_==2u&&!error_&&context_.preserved(c,held);
    }
private:
    Expectation e_;CooperativeContextWitness context_;
    const void* cpu_=nullptr;std::array<uint32_t,8> gqr_{};uint64_t last_=0;
    unsigned stage_=0,error_=0,visits_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
};
}
