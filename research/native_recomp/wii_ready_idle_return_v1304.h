#pragma once
#include "wii_reply_return_v1298.h"

namespace undercover::wii {
// Same CPU and same sleeping context, but the active idle context is
// restored by the original IRQ epilogue. No new IOS event, forced switch
// or modification of guest state. Attach only at the verified handler return.
class ReadyIdleReturnJoin {
public:
    unsigned stage()const{return stage_;}
    unsigned first_kind()const{return epoch_.first_kind();}
    unsigned failure()const{return error_;}
    const WakeReadyWitness* ready()const{return ready_;}
    template<class C>bool begin(C& c,const ReplyReturnWitness& returned,
            const WakeReadyWitness& ready,ExternalReturnWitness& frame,bool held){
        if(stage_||error_)return fail(1);
        epoch_=OpenTransactionEpoch(returned.first_kind());
        const auto s=NativeIosBinding::cold_snapshot();
        if(!epoch_held()||!s||!returned.returned(c,held)||frame.stage()!=1u||
           !ready.ready_context_held(c,held)||!ready.ready_storage_held(c,frame,held)||
           s->steps!=epoch_.reply_steps()||s->queued||s->replies||s->event||
           (s->control&(IpcMailbox::X1|IpcMailbox::Y1|IpcMailbox::Y2))||
           (s->flags&HollywoodIrq::IPC_PPC)||(s->pi_cause&s->pi_mask))return fail(1);
        if(!s->arm||(s->arm&31u)||s->arm!=s->ppc)return fail(1);
        for(unsigned i=0;i<words_.size();++i){
            auto w=NativeIosBinding::read_physical_word(s->arm+4u*i);if(!w)return fail(1);
            words_[i]=*w;
        }
        if(words_[0]!=StmIos::Reply||words_[1]!=epoch_.result_fd()||words_[2]!=StmIos::Open)return fail(1);
        cpu_=&c;frame_=&frame;ready_=&ready;mail_=*s;tick_=c.inst_count;stage_=1;
        return true;
    }
    template<class C>bool boundary(C& c,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return !error_&&stage_==1u&&cpu_==&c&&frame_&&ready_&&s&&
            c.inst_count>=tick_&&c.inst_count-tick_<=2048u&&
            epoch_held()&&same_scheduler_ipc_snapshot(mail_,*s)&&wire()&&ready_->ready_storage_held(c,*frame_,held);
    }
    template<class C>bool finish(C& c,bool held){
        if(!boundary(c,held)||c.inst_count==tick_||
           !frame_->cleared_restored(c,mail_.pi_cause,mail_.pi_mask))return fail(2);
        end_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool resumed_idle(C& c,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return !error_&&stage_==2u&&cpu_==&c&&frame_&&ready_&&s&&
            c.inst_count==end_&&epoch_held()&&same_scheduler_ipc_snapshot(mail_,*s)&&wire()&&
            frame_->cleared_restored(c,mail_.pi_cause,mail_.pi_mask)&&
            ready_->ready_storage_held(c,*frame_,held);
    }
    template<class C>bool selection_transport_held(C& c,bool held)const{
        return completed_transport_held(c,held)&&wire();
    }
    // After authenticated free and return, the next allocator may reuse
    // the old reply buffer. Keep the mailbox identity but not retired bytes.
    template<class C>bool completed_transport_held(C& c,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return completed_cpu_held(c,held)&&s&&epoch_held()&&same_scheduler_ipc_snapshot(mail_,*s);
    }
    // Only the completed CPU provenance here; the next transaction's
    // observer separately owns every subsequent mailbox transition.
    template<class C>bool completed_cpu_held(C& c,bool held)const{
        return held&&!error_&&stage_==2u&&cpu_==&c&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            c.inst_count>=end_&&c.inst_count-end_<=4096u;
    }
private:
    OpenTransactionEpoch epoch_{};
    bool epoch_held()const{return epoch_.valid()&&(!epoch_.second()||epoch_.acknowledged_descriptors(3u-epoch_.first_kind()));}
    const void* cpu_=nullptr;const WakeReadyWitness* ready_=nullptr;ExternalReturnWitness* frame_=nullptr;
    ColdIpcSnapshot mail_{};std::array<uint32_t,8> words_{};uint64_t tick_=0,end_=0;unsigned stage_=0,error_=0;
    bool wire()const{
        for(unsigned i=0;i<words_.size();++i)if(NativeIosBinding::read_physical_word(mail_.arm+4u*i)!=words_[i])return false;
        return true;
    }
    bool fail(unsigned n){if(!error_)error_=n;return false;}
};
}
