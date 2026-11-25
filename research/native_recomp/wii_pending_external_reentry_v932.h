#pragma once
#include "wii_external_return_v706.h"
namespace undercover::wii {
// After the real RFI has restored the first interrupted context, enter
// only the already asserted successor SI source. No ACK or mask write.
class PendingExternalReentry {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    ExternalReturnWitness& captured(){return second_;}
    template<class C,size_t N>bool enter(C& c,uint32_t cause,uint32_t mask,
                                        const std::array<uint8_t,N>& vector,bool restored,bool held){
        static_assert(N>=4&&N<=0x100&&N%4==0);
        if(stage_||error_||!restored||!held||!safe(c)||(cause&mask)!=8u||!(c.msr&0x8000u)||
           c.inst_count==UINT64_MAX)return fail(1);
        for(unsigned i=0;i<N;++i){
            if(!c.mmu.get_ptr(ExternalVector+i)||c.mmu.read8(ExternalVector+i)!=vector[i])return fail(1);
            vector_[i]=vector[i];
        }
        vector_size_=N;
        if(!second_.capture(c,cause,mask))return fail(1);
        cpu_=&c;cause_=cause;mask_=mask;tick_=c.inst_count;pc_=c.pc;msr_=c.msr;
        gp_=c.gpr;gqr_=c.gqr;cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        struct Source{uint32_t cause,mask;bool external_exception_pending(uint32_t msr)const{return (msr&0x8000u)&&(cause&mask)==8u;}};
        try{
            if(enter_external_irq(c,Source{cause,mask},vector,true)!=ExternalEntry::Entered)return fail(1);
        }catch(const std::exception&){return fail(1);}
        if(!state(c,cause,mask,held))return fail(1);
        stage_=1;return true;
    }
    template<class C>bool outer_poll(C& c,uint32_t cause,uint32_t mask,bool held){
        if(stage_!=1u||c.inst_count!=tick_||!state(c,cause,mask,held))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool vector_entry(C& c,uint32_t pc,uint32_t cause,uint32_t mask,bool held){
        if(stage_!=2u||pc!=ExternalVector||c.inst_count-tick_!=1u||!state(c,cause,mask,held))return fail(3);
        stage_=3;return true;
    }
private:
    ExternalReturnWitness second_;const void* cpu_=nullptr;
    unsigned stage_=0,error_=0;uint32_t cause_=0,mask_=0,pc_=0,msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0;
    uint64_t tick_=0;std::array<uint32_t,32> gp_{};std::array<uint32_t,8> gqr_{};
    std::array<uint8_t,256> vector_{};unsigned vector_size_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool state(C& c,uint32_t cause,uint32_t mask,bool held)const{
        if(!vector_size_)return false;
        for(unsigned i=0;i<vector_size_;++i)
            if(!c.mmu.get_ptr(ExternalVector+i)||c.mmu.read8(ExternalVector+i)!=vector_[i])return false;
        return !error_&&held&&cpu_==&c&&safe(c)&&cause==cause_&&mask==mask_&&(cause&mask)==8u&&
            c.pc==ExternalVector&&c.srr0==pc_&&c.srr1==(msr_&ExternalSrr1Mask)&&c.msr==(msr_&~ExternalMsrClear)&&
            c.gpr==gp_&&c.gqr==gqr_&&pack(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_;
    }
};
}
