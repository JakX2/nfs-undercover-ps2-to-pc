#pragma once
#include "native_external_irq.h"
#include "wii_irq_enable_witness_v615.h"
#include <array>
#include <cstdint>
namespace undercover::wii {
// Separate cold lane for the already asserted SI transfer-complete source.
// Never acknowledges the device or changes the interrupt mask. Stop before
// executing the original dispatcher; no original handler return is claimed.
struct ColdExternalExpectations {
    IrqEnableExpectations leaf;
    std::array<uint8_t,152> vector;
    uint32_t trampoline_word,dispatcher_word;
};
class ColdExternalEntry {
public:
    static constexpr uint32_t SI=8u,Thread=0x806f5318u,
        Trampoline=0x80526ce0u,Dispatcher=0x80526a3cu;
    explicit ColdExternalEntry(const ColdExternalExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    uint32_t vector_refusal()const noexcept{return vector_refusal_;}
    uint32_t dispatcher_refusal()const noexcept{return dispatcher_refusal_;}
    uint32_t saved_gpr_refusal()const noexcept{return saved_gpr_refusal_;}
    template<class C> bool begin(C& c,uint32_t cause,uint32_t mask){
        using W=IrqEnableWitness;
        if(stage_||error_||!c.is_running||c.in_callback||c.dispatch_saved_ctx||
           c.pc!=W::Call||c.lr!=W::Call||(c.msr&0x8000u)||(cause&mask)!=SI||
           !word(c,W::Call,e_.leaf.call_word)||!word(c,0x80000048u,0x004e5090u)||
           c.gpr[13]!=0x8070e8e0u||e_.leaf.resume<=W::Entry||
           e_.leaf.resume>W::Entry+16u||(e_.leaf.resume&3u)||!context(c)||!image(c))
            return fail(1);
        ctx_=&c;cause_=cause;mask_=mask;msr_=c.msr;last_=c.inst_count;
        stage_=1;return true;
    }
    template<class C> bool poll(C& c,uint32_t cause,uint32_t mask){
        return poll(c,cause,mask,[](C&,uint32_t,uint32_t){return true;});
    }
    template<class C,class Capture> bool poll(C& c,uint32_t cause,uint32_t mask,Capture&& capture){
        using W=IrqEnableWitness;
        if(!common(c,cause,mask))return fail(2);
        if(!(c.msr&0x8000u))return false; // masked source stays latched
        if(stage_!=2||c.pc!=e_.leaf.resume||c.lr!=W::Return||
           c.msr!=(msr_|0x8000u)||c.inst_count-entry_tick_!=(e_.leaf.resume-W::Entry)/4u||
           !word(c,c.pc,e_.leaf.resume_word)||!context(c)||!image(c))return fail(3);
        // Capture only after authenticating the exact pre-exception boundary.
        if(!capture(c,cause,mask))return fail(10);
        gp_=c.gpr;lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        resume_=c.pc;prior_=c.msr;
        struct Source {bool external_exception_pending(uint32_t msr)const{return (msr&0x8000u)!=0;}};
        try{
            if(enter_external_irq(c,Source{},e_.vector,true)!=ExternalEntry::Entered)return fail(3);
        }catch(const std::exception&){return fail(3);}
        if(c.pc!=ExternalVector||c.srr0!=resume_||c.srr1!=(prior_&ExternalSrr1Mask)||
           c.msr!=(prior_&~ExternalMsrClear)||c.gpr!=gp_||c.lr!=lr_||c.ctr!=ctr_||c.xer!=xer_)
            return fail(3);
        last_=c.inst_count;stage_=3;return true;
    }
    template<class C> bool observe(uint32_t addr,C& c,uint32_t cause,uint32_t mask){
        using W=IrqEnableWitness;
        if(!common(c,cause,mask)||c.pc!=addr||c.inst_count<last_||c.inst_count-last_>8192u)
            return fail(4);
        if(stage_==1){
            if(addr!=W::Entry||c.lr!=W::Return||c.msr!=msr_||
               c.inst_count<=last_||!word(c,addr,e_.leaf.entry_word))return fail(5);
            entry_tick_=c.inst_count;stage_=2;
        }else if(stage_==3){
            // The split outer dispatcher increments inst_count once after
            // process_pending_callbacks, BEFORE the first vector entry trace.
            // No guest instruction executes between these two boundaries.
            vector_refusal_=0;
            if(addr!=ExternalVector)vector_refusal_|=1u;
            if(c.inst_count-last_!=1u)vector_refusal_|=2u;
            if(!image(c))vector_refusal_|=4u;
            if(c.srr0!=resume_)vector_refusal_|=8u;
            if(c.srr1!=(prior_&ExternalSrr1Mask))vector_refusal_|=16u;
            if(c.msr!=(prior_&~ExternalMsrClear))vector_refusal_|=32u;
            if(c.gpr!=gp_)vector_refusal_|=64u;
            if(c.lr!=lr_)vector_refusal_|=128u;
            if(c.ctr!=ctr_)vector_refusal_|=256u;
            if(c.xer!=xer_)vector_refusal_|=512u;
            if(vector_refusal_)return fail(6);
            stage_=4;
        }else if(stage_==4){
            if(addr!=Trampoline||c.inst_count<=last_||(c.msr&0x8000u)||
               c.gpr[3]!=4||c.gpr[4]!=Thread||!word(c,addr,e_.trampoline_word)||!context(c)||
               !word(c,Thread+408u,resume_)||!word(c,Thread+412u,prior_&ExternalSrr1Mask)||
               !word(c,Thread+132u,lr_)||!word(c,Thread+136u,ctr_)||!word(c,Thread+140u,xer_))
                return fail(7);
            for(unsigned i=3;i<=5;++i)if(!word(c,Thread+4*i,gp_[i]))return fail(7);
            stage_=5;
        }else if(stage_==5){
            dispatcher_refusal_=saved_gpr_refusal_=0;
            if(addr!=Dispatcher)dispatcher_refusal_|=1u;
            if(c.inst_count<=last_)dispatcher_refusal_|=2u;
            if(c.msr&0x8000u)dispatcher_refusal_|=4u;
            if(c.gpr[3]!=4)dispatcher_refusal_|=8u;
            if(c.gpr[4]!=Thread)dispatcher_refusal_|=16u;
            if(!word(c,Dispatcher,e_.dispatcher_word))dispatcher_refusal_|=32u;
            if(!word(c,Thread+408u,resume_))dispatcher_refusal_|=64u;
            if(!word(c,Thread+412u,prior_&ExternalSrr1Mask))dispatcher_refusal_|=128u;
            for(unsigned i=6;i<32;++i)
                if(!word(c,Thread+4*i,gp_[i]))saved_gpr_refusal_|=uint32_t(1u)<<i;
            if(saved_gpr_refusal_)dispatcher_refusal_|=256u;
            if(dispatcher_refusal_)return fail(8);
            stage_=6;
        }else return fail(4);
        last_=c.inst_count;return true;
    }
private:
    ColdExternalExpectations e_;
    const void* ctx_=nullptr;unsigned stage_=0,error_=0;
    uint32_t vector_refusal_=0,dispatcher_refusal_=0,saved_gpr_refusal_=0;
    uint32_t cause_=0,mask_=0,msr_=0,prior_=0,resume_=0,lr_=0,ctr_=0,xer_=0;
    uint64_t last_=0,entry_tick_=0;
    std::array<uint32_t,32> gp_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C> bool common(C& c,uint32_t cause,uint32_t mask)const{
        return !error_&&stage_>=1&&stage_<6&&ctx_==&c&&c.is_running&&!c.in_callback&&
            !c.dispatch_saved_ctx&&cause==cause_&&mask==mask_&&(cause&mask)==SI;
    }
    template<class C> static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&
            c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C> static bool context(C& c){
        return word(c,0x800000d4u,Thread)&&word(c,0x800000e4u,Thread)&&
            word(c,0x800000c0u,Thread&0x3fffffffu)&&word(c,0x80003010u,Trampoline)&&
            word(c,0x80003090u,0x80531b34u);
    }
    template<class C> bool image(C& c)const{
        // The vector is a fixed small array. Keep guest addresses uint32_t
        // on both 32-bit PPC and 64-bit Windows without implicit size_t narrowing.
        constexpr uint32_t LastVectorOffset =
            uint32_t(std::tuple_size_v<decltype(e_.vector)>-1u);
        if(!c.mmu.get_ptr(ExternalVector)||
           !c.mmu.get_ptr(ExternalVector+LastVectorOffset))return false;
        for(unsigned i=0;i<e_.vector.size();++i)
            if(c.mmu.read8(ExternalVector+i)!=e_.vector[i])return false;
        return true;
    }
};
}
