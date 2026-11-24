#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
struct IrqEnableExpectations {uint32_t call_word,entry_word,resume,resume_word,return_word;};
// Quiescent cold-start lane. A pending IRQ is a separate execution path,
// not grounds to ignore a callback or suppress an interrupt.
class IrqEnableWitness {
public:
    static constexpr uint32_t Call=0x80520944u,Entry=0x805265c0u,Return=Call+4u;
    explicit IrqEnableWitness(IrqEnableExpectations e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c,uint32_t cause,uint32_t mask){
        if(stage_||error_||!c.is_running||c.pc!=Call||c.lr!=Call||
           (c.msr&0x8000u)||c.dispatch_saved_ctx||(cause&mask)||
           !equal(c,Call,e_.call_word)||!equal(c,0x80000048u,0x004e5090u)||
           c.gpr[13]!=0x8070e8e0u||e_.resume<=Entry||e_.resume>Entry+16u||(e_.resume&3u))
            return fail(1);
        ctx_=&c;msr_=c.msr;ctr_=c.ctr;srr0_=c.srr0;srr1_=c.srr1;gprs_=c.gpr;
        cause_=cause;mask_=mask;last_=c.inst_count;stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c,uint32_t cause,uint32_t mask){
        if(error_||stage_<1||stage_>3||ctx_!=&c||!c.is_running||
           c.dispatch_saved_ctx||c.pc!=addr||c.lr!=Return||c.inst_count<=last_||
           cause!=cause_||mask!=mask_||(cause&mask)||c.ctr!=ctr_||
           c.srr0!=srr0_||c.srr1!=srr1_||c.gpr[1]!=gprs_[1]||
           c.gpr[2]!=gprs_[2]||c.gpr[13]!=gprs_[13]||
           !equal(c,0x80000048u,0x004e5090u))return fail(2);
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gprs_[i])return fail(2);
        switch(stage_){
        case 1:
            if(addr!=Entry||c.msr!=msr_||!equal(c,Call,e_.call_word)||!equal(c,Entry,e_.entry_word))return fail(3);
            entry_tick_=c.inst_count;break;
        case 2:
            if(addr!=e_.resume||c.msr!=(msr_|0x8000u)||!equal(c,addr,e_.resume_word)||
               c.inst_count-entry_tick_!=(e_.resume-Entry)/4u)return fail(4);
            break;
        case 3:
            if(addr!=Return||c.gpr[3]!=0||c.msr!=(msr_|0x8000u)||
               !equal(c,Return,e_.return_word)||c.inst_count-entry_tick_!=5u)return fail(5);
            break;
        }
        ++stage_;last_=c.inst_count;return true;
    }
private:
    IrqEnableExpectations e_;
    const void* ctx_=nullptr;unsigned stage_=0,error_=0;
    uint32_t msr_=0,ctr_=0,srr0_=0,srr1_=0,cause_=0,mask_=0;
    uint64_t last_=0,entry_tick_=0;
    std::array<uint32_t,32> gprs_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
};
}
