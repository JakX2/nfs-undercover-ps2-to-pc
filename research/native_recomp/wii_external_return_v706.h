#pragma once
#include "native_external_irq.h"
#include <array>
#include <cstdint>
#ifndef UNDERCOVER_WII_GUEST_ONLY_DISPATCH
#define UNDERCOVER_WII_GUEST_ONLY_DISPATCH 0
#endif
static_assert(UNDERCOVER_WII_GUEST_ONLY_DISPATCH == 0 ||
              UNDERCOVER_WII_GUEST_ONLY_DISPATCH == 1,
              "unknown native dispatch guest tick policy");

namespace undercover::wii {
// Read-only same-thread integer context witness. Does not claim FPU
// ownership or a scheduler context switch, and never performs RFI itself.
class ExternalReturnWitness {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    uint32_t source()const{return source_;}
    template<class C>bool capture(C& c,uint32_t cause,uint32_t mask,uint32_t source=8u){
        if(stage_||error_||!safe(c)||!c.pc||(c.pc&3u)||!(c.msr&0x8000u)||
           !source||(source&(source-1u))||(cause&mask)!=source||c.inst_count>UINT64_MAX-32768u)return fail(1);
        ctx_=&c;gp_=c.gpr;cr_=pack_cr(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;
        resume_=c.pc;restored_msr_=c.msr&ExternalSrr1Mask;
        source_=source;cause_=cause&~source;mask_=mask;start_tick_=c.inst_count;stage_=1;return true;
    }
    struct SavedIntegerCheck{
        unsigned gpr_mismatches=0,special_mask=0;
        uint32_t gpr_mask=0;
        bool valid=false;
        bool ok()const{return valid&&!gpr_mismatches&&!special_mask;}
    };
    // The original vector/trampoline must actually have saved the captured
    // integer context, including the CR and previously unobserved r0-r2.
    // This read-only check never changes the later RFI witness stage.
    template<class C>SavedIntegerCheck saved_integer(C& c,uint32_t base)const{
        SavedIntegerCheck out;
        if(stage_!=1||error_||ctx_!=&c||!safe(c)||(c.msr&0x8000u)||
           (base&3u)||base<0x80000000u||uint64_t(base)+416u>0x81800000u||
           c.inst_count<=start_tick_||c.inst_count-start_tick_>32768u)return out;
        auto same=[&](uint32_t off,uint32_t v){
            const auto a=base+off;
            return c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==v;
        };
        for(unsigned i=0;i<32;++i)if(!same(i*4u,gp_[i])){++out.gpr_mismatches;out.gpr_mask|=1u<<i;}
        const std::array<uint32_t,6> offsets{128u,132u,136u,140u,408u,412u};
        const std::array<uint32_t,6> values{cr_,lr_,ctr_,xer_,resume_,restored_msr_};
        for(unsigned i=0;i<offsets.size();++i)if(!same(offsets[i],values[i]))out.special_mask|=1u<<i;
        out.valid=true;return out;
    }
    template<class C>bool before_rfi(C& c,uint32_t pc,uint32_t word,uint32_t cause,uint32_t mask){
        return before_rfi_impl(c,pc,word,cause,mask,false);
    }
    // A second, already completed SI token can remain asserted across RFI.
    // The caller must separately authenticate that token and the device.
    template<class C>bool pending_source(C& c,uint32_t cause,uint32_t mask)const{
        return stage_==1u&&pending_common(c,cause,mask);
    }
    // Re-check the exact CPU and native RFI boundary before re-entry.
    template<class C>bool pending_restored(C& c,uint32_t cause,uint32_t mask)const{
        return stage_==3u&&pending_return_&&pending_common(c,cause,mask)&&restored(c)&&
               (c.msr&0x8000u)&&c.inst_count==rfi_tick_;
    }
    // Exact cleared-IRQ handoff after both generated RFI polls, before
    // a single resumed native instruction. Does not advance the witness.
    template<class C>bool cleared_restored(C& c,uint32_t cause,uint32_t mask)const{
        return stage_==4u&&!pending_return_&&common(c,cause,mask)&&restored(c)&&
               (c.msr&0x8000u)&&c.inst_count==rfi_tick_;
    }
    template<class C>bool before_pending_rfi(C& c,uint32_t pc,uint32_t word,uint32_t cause,uint32_t mask){
        return before_rfi_impl(c,pc,word,cause,mask,true);
    }
    template<class C>bool pending_rfi_return(C& c,uint32_t cause,uint32_t mask){
        if(stage_!=2u||!pending_return_||!pending_common(c,cause,mask)||!restored(c)||
           !(c.msr&0x8000u)||c.inst_count!=rfi_tick_)return fail(3);
        stage_=3;return true;
    }
private:
    template<class C>bool before_rfi_impl(C& c,uint32_t pc,uint32_t word,uint32_t cause,uint32_t mask,bool pending){
        if(stage_!=1||!(pending?pending_common(c,cause,mask):common(c,cause,mask))||c.msr&0x8000u||
           !pc||(pc&3u)||word!=0x4c000064u||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
           c.mmu.read32(pc)!=word||c.inst_count<=start_tick_||c.inst_count-start_tick_>32768u||
           c.srr0!=resume_||c.srr1!=restored_msr_||!integer_state(c))return fail(2);
        pending_return_=pending;rfi_tick_=c.inst_count;stage_=2;return true;
    }
public:
    template<class C>bool poll(C& c,uint32_t cause,uint32_t mask){
        // First is generated RFI's rising EE callback, second is the
        // subsequent outer dispatcher poll. No native guest instruction
        // or HLE context restore may execute between them.
        if(pending_return_||(stage_!=2&&stage_!=3)||!common(c,cause,mask)||!restored(c)||
           c.inst_count!=rfi_tick_)return fail(3);
        ++stage_;return true;
    }
    template<class C>bool resume(C& c,uint32_t pc,uint32_t word,uint32_t cause,uint32_t mask){
        // Hook after ++inst_count at the original resume label. The
        // legacy dispatcher adds one host tick; V438 adds none.
        if(pending_return_||stage_!=4||!common(c,cause,mask)||!restored(c)||pc!=resume_||
           c.inst_count-rfi_tick_!=uint64_t(2u-UNDERCOVER_WII_GUEST_ONLY_DISPATCH)||
           !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||
           c.mmu.read32(pc)!=word)return fail(4);
        stage_=5;return true;
    }
private:
    const void* ctx_=nullptr;unsigned stage_=0,error_=0;
    std::array<uint32_t,32> gp_{};
    uint32_t cr_=0,lr_=0,ctr_=0,xer_=0,resume_=0,restored_msr_=0,cause_=0,mask_=0;
    uint64_t start_tick_=0,rfi_tick_=0;
    uint32_t source_=0;
    bool pending_return_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack_cr(C& c){
        uint32_t value=0;
        for(const auto& f:c.cr)value=(value<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
        return value;
    }
    template<class C>bool integer_state(C& c)const{
        return c.gpr==gp_&&pack_cr(c)==cr_&&c.lr==lr_&&c.ctr==ctr_&&c.xer==xer_;
    }
    template<class C>bool restored(C& c)const{
        return c.pc==resume_&&c.msr==restored_msr_&&c.srr0==resume_&&c.srr1==restored_msr_&&integer_state(c);
    }
    template<class C>bool pending_common(C& c,uint32_t cause,uint32_t mask)const{
        return !error_&&ctx_==&c&&safe(c)&&cause==(cause_|source_)&&mask==mask_&&(cause&mask)==source_;
    }
    template<class C>bool common(C& c,uint32_t cause,uint32_t mask)const{
        return !error_&&ctx_==&c&&safe(c)&&cause==cause_&&mask==mask_&&!(cause&mask);
    }
};
}
