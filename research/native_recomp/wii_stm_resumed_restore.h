#pragma once
#include "wii_stm_outer_restore.h"
#include <bit>
namespace undercover::wii {
// Read-only witness for the original OSRestoreInterrupts suffix after
// the third native RFI. The native emitter executes every instruction.
// This observer predicts only bounded, register-only leaf operations.
class StmResumedRestoreWitness {
public:
    explicit StmResumedRestoreWitness(StmOuterRestoreExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    template<class C>bool begin(C& c,bool authenticated){
        if(stage_||error_||!authenticated||!safe(c)||!(c.msr&0x8000u)||
           c.pc!=e_.resume||c.lr!=e_.caller||c.srr0!=e_.resume||
           !known(c,e_.resume,e_.resume_word)||!word(c,e_.caller,e_.caller_word))return fail(1);
        cpu_=&c;gp_=c.gpr;gqr_=c.gqr;msr_=c.msr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;next_=e_.resume;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held,bool rfi_label){
        if(stage_!=1u||!common(c,held)||return_due_||pc!=next_||
           c.inst_count-last_!=(visits_?1u:2u)||rfi_label!=(visits_==0u)||
           (!visits_&&(!initial_poll_||c.pc!=pc))||!known(c,pc,w)||++visits_>8u)return fail(2);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        if(w==0x4e800020u){
            return_due_=true;next_=e_.caller;return true;
        }
        if(w==0x4c00012cu||w==0x7c0004acu){} // isync/sync, no integer changes
        else if(op==21u&&!(w&1u)&&volatile_reg(ra)){
            gp_[ra]=std::rotl(gp_[rs],int(rb))&mask((w>>6)&31u,(w>>1)&31u);
        }else if(op==14u&&volatile_reg(rs)){
            gp_[rs]=(ra?gp_[ra]:0u)+uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        }else if(op==24u&&volatile_reg(ra)){
            gp_[ra]=gp_[rs]|(w&0xffffu);
        }else if(op==31u&&xo==444u&&!(w&1u)&&volatile_reg(ra)){
            gp_[ra]=gp_[rs]|gp_[rb];
        }else return fail(3);
        if(!known(c,next_,c.mmu.get_ptr(next_)&&c.mmu.get_ptr(next_+3u)?c.mmu.read32(next_):0u))return fail(3);
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held)||c.inst_count!=last_)return fail(4);
        if(!visits_&&!initial_poll_&&c.pc==e_.resume){initial_poll_=true;return true;}
        if(!return_due_||c.pc!=e_.caller||!word(c,e_.caller,e_.caller_word))return fail(4);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&return_due_&&common(c,held)&&c.inst_count==last_&&
            c.pc==e_.caller&&word(c,e_.caller,e_.caller_word);
    }
private:
    StmOuterRestoreExpectation e_;const void* cpu_=nullptr;
    std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0,next_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0;
    bool initial_poll_=false,return_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool volatile_reg(unsigned r){return r==0u||(r>=3u&&r<=12u);}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t out=0;
        for(unsigned n=mb;;n=(n+1u)&31u){out|=1u<<(31u-n);if(n==me)break;}
        return out;
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool common(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.gpr==gp_&&c.gqr==gqr_&&c.msr==msr_&&
            pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_&&c.srr0==srr0_&&c.srr1==srr1_;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        if((a&3u)||a<0x80000000u||a>0x817ffffcu)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+3u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+3u&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t pc,uint32_t w)const{
        return std::count_if(e_.words.begin(),e_.words.end(),
            [&](auto x){return x.owner==e_.root&&x.pc==pc&&x.word==w;})==1&&word(c,pc,w);
    }
};
}
