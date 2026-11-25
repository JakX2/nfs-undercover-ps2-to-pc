#pragma once
#include "wii_external_return_v706.h"
#include <array>
#include <bit>
#include <cstdint>
namespace undercover::wii {
struct IrqLeafFinishExpectation {uint32_t resume,extract,caller,caller_word;};
// Read-only proof of original previous-EE extraction, BLR and dispatch.
class IrqLeafFinishWitness {
public:
    explicit IrqLeafFinishWitness(IrqLeafFinishExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    static bool shape(uint32_t w){
        return w>>26==21u&&!(w&1u)&&((w>>16)&31u)==3u&&
               ((w>>11)&31u)==17u&&((w>>6)&31u)==31u&&((w>>1)&31u)==31u;
    }
    template<class C>bool start(C& c,const ExternalReturnWitness& restored,bool previous_ee,uint32_t pc,uint32_t w,bool held){
        if(stage_||error_||restored.stage()!=5u||!held||!safe(c)||!(c.msr&0x8000u)||
           pc!=e_.resume||c.pc!=pc||w!=e_.extract||!shape(w)||c.lr!=e_.caller||
           !word(c,pc,w)||!word(c,pc+4u,0x4e800020u)||!word(c,e_.caller,e_.caller_word)||
           c.inst_count>UINT64_MAX-4u)return fail(1);
        const auto result=std::rotl(c.gpr[(w>>21)&31u],17)&1u;
        if(result!=unsigned(previous_ee))return fail(1);
        cpu_=&c;gp_=c.gpr;gp_[3]=result;cr_=pack(c);
        ctr_=c.ctr;xer_=c.xer;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;gqr_=c.gqr;
        tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before_blr(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||pc!=e_.resume+4u||w!=0x4e800020u||
           !word(c,pc,w)||c.inst_count!=tick_+1u)return fail(2);
        stage_=2;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=2u||!common(c,held)||c.pc!=e_.caller||c.inst_count!=tick_+1u)return fail(3);
        stage_=3;return true;
    }
    template<class C>bool dispatch(C& c,uint32_t pc,bool held){
        if(stage_!=3u||!common(c,held)||pc!=e_.caller||c.pc!=pc||c.inst_count!=tick_+2u)return fail(4);
        stage_=4;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=4u||!common(c,held)||pc!=e_.caller||c.pc!=pc||
           w!=e_.caller_word||!word(c,pc,w)||c.inst_count!=tick_+3u)return fail(5);
        stage_=5;return true;
    }
private:
    IrqLeafFinishExpectation e_;const void* cpu_=nullptr;unsigned stage_=0,error_=0;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    uint32_t cr_=0,ctr_=0,xer_=0,msr_=0,srr0_=0,srr1_=0;uint64_t tick_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){
        uint32_t r=0;for(auto f:c.cr)r=(r<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return r;
    }
    template<class C>static bool word(C& c,uint32_t pc,uint32_t w){
        return !(pc&3u)&&pc>=0x80000000u&&pc<=0x817ffffcu&&c.mmu.get_ptr(pc)&&c.mmu.get_ptr(pc+3u)&&c.mmu.read32(pc)==w;
    }
    template<class C>bool common(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&pack(c)==cr_&&c.lr==e_.caller&&
            c.ctr==ctr_&&c.xer==xer_&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&c.gqr==gqr_;
    }
};
}
