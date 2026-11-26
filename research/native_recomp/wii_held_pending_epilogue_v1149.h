#pragma once
#include "wii_third_alarm_suffix_v1047.h"
#include "wii_third_pending_reentry_v1067.h"
namespace undercover::wii {
// Join the actual held handler return to the real scheduler/context loader.
// Only the existing external-exception entry routine changes CPU state;
// the native RFI and all guest instructions remain emitter-owned.
class HeldPendingEpilogueWitness {
public:
    enum class PollResult{Rejected,Continue,Entered};
    HeldPendingEpilogueWitness(LiveEpilogueExpectation ep,SecondVectorExpectation vec):expected_(ep),ep_(ep),next_(vec){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned epilogue_failure()const{return ep_.failure();}
    unsigned reentry_failure()const{return next_.failure();}
    unsigned visits()const{return ep_.visits();}
    unsigned vector_visits()const{return next_.vector_visits();}
    unsigned trampoline_visits()const{return next_.trampoline_visits();}
    // Bind only the actual controller and PI atomics retained by the device.
    template<class C>bool begin_bound(C& c,uint32_t pc,uint32_t w,const HeldHandlerReturnWitness& prior,
            ExternalReturnWitness& frame,PostAckTransferDevice& dev){
        if(!dev.ctl_||!dev.cause_||!dev.mask_)return fail(1);
        return begin(c,pc,w,prior,frame,dev,*dev.ctl_,*dev.cause_,*dev.mask_);
    }
    template<class C>bool begin(C& c,uint32_t pc,uint32_t w,const HeldHandlerReturnWitness& prior,
            ExternalReturnWitness& frame,PostAckTransferDevice& dev,SiController& ctl,
            const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask){
        if(stage_||error_||pc!=expected_.dispatcher||
           !prior.finished_at(c,pc,w,dev,frame,expected_.context)||
           !dev.owns_completed(ctl,cause,mask,c.inst_count,3u)||!no_si(c,w)||
           !ep_.begin_pending(c,frame,cause.load(),mask.load())||
           !ep_.before(c,pc,w,cause.load(),mask.load()))return fail(1);
        cpu_=&c;frame_=&frame;dev_=&dev;ctl_=&ctl;cause_=&cause;mask_=&mask;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w){
        if(stage_==4u)return same(c)&&no_si(c,w)&&next_.before(c,pc,w)?true:fail(5);
        if(stage_!=1u||!same(c)||!no_si(c,w)||c.inst_count-last_!=1u||
           !dev_->after_return_at(c.inst_count)||!frame_->saved_integer(c,expected_.context).ok())return fail(2);
        last_=c.inst_count;
        if(!held(c)||!ep_.before(c,pc,w,cause_->load(),mask_->load()))return fail(2);
        if(ep_.stage()==2u)stage_=2u;
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc){
        if(stage_==3u){
            if(!same(c)||!next_.vector_entry(c,pc))return fail(5);
            stage_=4u;return true;
        }
        if(stage_==4u){
            if(!same(c)||!next_.entry(c,pc))return fail(5);
            if(next_.stage()==4u)stage_=5u;
            return true;
        }
        return stage_==1u&&held(c)&&frame_->saved_integer(c,expected_.context).ok()&&
               ep_.entry(c,pc,cause_->load(),mask_->load())?true:fail(3);
    }
    template<class C,size_t N>PollResult poll(C& c,const std::array<uint8_t,N>& image){
        if(stage_==4u)return same(c)&&next_.poll(c)?PollResult::Continue:reject(5);
        if(stage_==3u)return same(c)&&next_.outer_poll(c)?PollResult::Continue:reject(5);
        if(!held(c))return reject(4);
        if(stage_==1u)return frame_->saved_integer(c,expected_.context).ok()&&
            ep_.poll(c,cause_->load(),mask_->load())?PollResult::Continue:reject(4);
        if(stage_!=2u||!ep_.pending_rfi_return(c,cause_->load(),mask_->load())||
           !next_.enter(c,*frame_,*dev_,*ctl_,*cause_,*mask_,image))return reject(4);
        stage_=3u;return PollResult::Entered;
    }
    template<class C>bool saved(C& c){return stage_==5u&&same(c)&&next_.saved(c,expected_.context);}
    ThirdPendingReentry& next(){return next_;}
private:
    LiveEpilogueExpectation expected_;LiveEpilogueWitness ep_;ThirdPendingReentry next_;
    const void* cpu_=nullptr;ExternalReturnWitness* frame_=nullptr;PostAckTransferDevice* dev_=nullptr;SiController* ctl_=nullptr;
    const std::atomic<uint32_t>* cause_=nullptr,*mask_=nullptr;
    uint64_t last_=0;unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    PollResult reject(unsigned n){fail(n);return PollResult::Rejected;}
    template<class C>bool same(C& c)const{return !error_&&cpu_==&c&&frame_&&dev_&&ctl_&&cause_&&mask_;}
    template<class C>bool held(C& c)const{return same(c)&&last_==c.inst_count&&dev_->owns_completed(*ctl_,*cause_,*mask_,c.inst_count,3u);}
    template<class C>static bool no_si(C& c,uint32_t w){
        const auto a=PostAckTransferDevice::word_access(c,w);const uint32_t phys=a.address&0x3fffffffu;
        return !PostAckTransferDevice::offset(a.address)&&
            !(phys<0x0d006500u&&uint64_t(phys)+4u>0x0d006400u)&&
            !(phys<0x0d806500u&&uint64_t(phys)+4u>0x0d806400u);
    }
};
}
