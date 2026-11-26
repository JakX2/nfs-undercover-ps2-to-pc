#pragma once
#include "wii_second_vector_v939.h"
#include "wii_second_si_dispatch_v944.h"
#include "wii_second_completion_ack_v950.h"
#include "wii_bounded_ack_call_route_v956.h"
namespace undercover::wii {
// Compose the completed third SI owner with a real restored RFI context.
// No host-supplied "held" boolean, no device writes and no scheduler advance.
// The caller must advance the scheduler before each new native tick.
class ThirdPendingReentry {
public:
    explicit ThirdPendingReentry(SecondVectorExpectation e):vector_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned vector_failure()const{return vector_.failure();}
    unsigned vector_visits()const{return vector_.vector_visits();}
    unsigned trampoline_visits()const{return vector_.trampoline_visits();}
    template<class C,size_t N>bool enter(C& c,ExternalReturnWitness& prior,PostAckTransferDevice& dev,
             SiController& ctl,const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
             const std::array<uint8_t,N>& image){
        if(stage_||error_||!prior.pending_restored(c,cause.load(),mask.load())||
           !dev.owns_completed(ctl,cause,mask,c.inst_count,3u)||
           !next_.enter(c,cause.load(),mask.load(),image,true,true))return fail(1);
        cpu_=&c;dev_=&dev;ctl_=&ctl;cause_=&cause;mask_=&mask;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool outer_poll(C& c){
        if(stage_!=1u||!held(c)||!next_.outer_poll(c,cause_->load(),mask_->load(),true))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool vector_entry(C& c,uint32_t pc){
        if(stage_!=2u||!advance(c)||!next_.vector_entry(c,pc,cause_->load(),mask_->load(),true)||
           !vector_.begin(c,next_,cause_->load(),mask_->load(),true))return fail(3);
        stage_=3;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t word){
        return stage_==3u&&advance(c)&&vector_.before(c,pc,word,cause_->load(),mask_->load(),true)?true:fail(4);
    }
    template<class C>bool poll(C& c){
        return stage_==3u&&held(c)&&vector_.poll(c,cause_->load(),mask_->load(),true)?true:fail(5);
    }
    template<class C>bool entry(C& c,uint32_t pc){
        if(stage_!=3u||!(c.inst_count==last_?held(c):advance(c))||
           !vector_.entry(c,pc,cause_->load(),mask_->load(),true))return fail(6);
        if(vector_.stage()==3u)stage_=4;
        return true;
    }
    template<class C>bool saved(C& c,uint32_t context){
        return stage_==4u&&held(c)&&next_.captured().saved_integer(c,context).ok();
    }
    // Only the completed vector can join the newly captured frame to
    // the original SI dispatcher. The retired second capture is not reused.
    template<class C>bool begin_dispatch(C& c,SecondSiDispatchWitness& dispatch){
        if(stage_!=4u||!held(c)||!dispatch.begin(c,next_.captured(),cause_->load(),mask_->load(),true))return fail(7);
        dispatch_=&dispatch;stage_=5;return true;
    }
    template<class C>bool dispatch_tick(C& c){
        if(stage_!=5u||!dispatch_||!advance(c)||!dispatch_->poll(c,cause_->load(),mask_->load(),true))return fail(8);
        return true;
    }
    template<class C>bool dispatch_entry(C& c,uint32_t pc){
        if(stage_!=5u||!dispatch_||!(c.inst_count==last_?held(c):advance(c))||
           !dispatch_->observe(c,pc,cause_->load(),mask_->load(),true))return fail(9);
        if(dispatch_->stage()==6u)stage_=6u;
        return true;
    }
    template<class C>bool dispatch_poll(C& c){
        return stage_==5u&&dispatch_&&held(c)&&dispatch_->poll(c,cause_->load(),mask_->load(),true)?true:fail(8);
    }
    template<class C>bool dispatch_saved(C& c,uint32_t context){
        return stage_==6u&&held(c)&&next_.captured().saved_integer(c,context).ok();
    }
    // Transfer the completed token only after authenticating the new
    // handler and its independently supplied native call geometry. The
    // previous transfer observer is retired, never reset or reused.
    template<class C>bool begin_ack(C& c,std::span<const AckCallSpan> spans,
            std::span<const AckCallEdge> edges,std::span<const AckMsrSite> msr={}){
        if(stage_!=6u||!held(c)||!dispatch_||!dispatch_->handler_ready(c,cause_->load(),mask_->load())||
           c.pc!=SiDispatchWitness::Handler||c.gpr[3]!=20u||c.gpr[4]!=SiDispatchWitness::Thread||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           spans.empty()||spans.front().root!=SiDispatchWitness::Handler||
           !ack_calls_.begin(c,spans,edges,msr,true)||
           !dev_->handoff_second_ack(ack_,*ctl_,*cause_,*mask_,c.inst_count))return fail(10);
        stage_=7u;return true;
    }
    template<class C>bool ack_before(C& c,uint32_t owner,uint32_t pc,uint32_t w){
        if(!ack_frame(c)||!ack_.before(c,pc,w,true)||!ack_calls_.before(c,pc,w,owner))return fail(11);
        if(ack_.stage()==3u){
            if(ack_.token()!=3u||!ack_.reads()||!ack_.writes()||!ack_calls_.entries()||
               !ack_calls_.returns()||!ack_.response_class_verified())return fail(11);
            stage_=8u;
        }
        return true;
    }
    template<class C>bool ack_entry(C& c,uint32_t pc){
        return ack_frame(c)&&ack_calls_.entry(c,pc)&&ack_.poll(c.inst_count)?true:fail(12);
    }
    template<class C>bool ack_poll(C& c){
        return ack_frame(c)&&ack_calls_.can_poll()&&ack_.poll(c.inst_count)?true:fail(13);
    }
    bool ack_read(unsigned off,uint32_t& v){
        return stage_==7u&&!error_&&ack_.read(*ctl_,off,v)?true:fail(14);
    }
    bool ack_write(unsigned off,uint32_t v){
        return stage_==7u&&!error_&&ack_.write(*ctl_,off,v)?true:fail(15);
    }
    const SecondCompletionAck& completion_ack()const{return ack_;}
    const BoundedAckCallRoute& ack_calls()const{return ack_calls_;}
private:
    template<class C>bool ack_frame(C& c)const{
        return stage_==7u&&!error_&&cpu_==&c&&dev_&&dev_->stage()==3u&&
               next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok();
    }
    SecondCompletionAck ack_;
    BoundedAckCallRoute ack_calls_;
    SecondSiDispatchWitness* dispatch_=nullptr;
    PendingExternalReentry next_;
    SecondVectorWitness vector_;
    const void* cpu_=nullptr;PostAckTransferDevice* dev_=nullptr;SiController* ctl_=nullptr;
    const std::atomic<uint32_t>* cause_=nullptr,*mask_=nullptr;
    uint64_t last_=0;unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>bool held(C& c)const{
        return !error_&&cpu_==&c&&c.inst_count==last_&&dev_&&ctl_&&cause_&&mask_&&
               dev_->owns_completed(*ctl_,*cause_,*mask_,c.inst_count,3u);
    }
    template<class C>bool advance(C& c){
        if(error_||cpu_!=&c||!dev_||c.inst_count-last_!=1u||!dev_->after_return_at(c.inst_count))return false;
        last_=c.inst_count;return held(c);
    }
};
}
