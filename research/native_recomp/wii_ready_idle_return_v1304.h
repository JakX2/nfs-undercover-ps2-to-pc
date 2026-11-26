#pragma once
#include "wii_reply_return_v1298.h"

namespace undercover::wii {
// Same CPU and same sleeping context, but the active idle context is
// restored by the original IRQ epilogue. No new IOS event, forced switch
// or modification of guest state. Attach only at the verified handler return.
class ReadyIdleReturnJoin {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    template<class C>bool begin(C& c,const ReplyReturnWitness& returned,
            const WakeReadyWitness& ready,ExternalReturnWitness& frame,bool held){
        const auto s=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!s||!returned.returned(c,held)||frame.stage()!=1u||
           !ready.ready_context_held(c,held)||!ready.ready_storage_held(c,frame,held)||
           s->steps!=2u||s->queued||s->replies||s->event||
           (s->control&(IpcMailbox::X1|IpcMailbox::Y1|IpcMailbox::Y2))||
           (s->flags&HollywoodIrq::IPC_PPC)||(s->pi_cause&s->pi_mask))return fail(1);
        cpu_=&c;frame_=&frame;ready_=&ready;mail_=*s;tick_=c.inst_count;stage_=1;
        return true;
    }
    template<class C>bool boundary(C& c,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return !error_&&stage_==1u&&cpu_==&c&&frame_&&ready_&&s&&
            c.inst_count>=tick_&&c.inst_count-tick_<=2048u&&
            same_scheduler_ipc_snapshot(mail_,*s)&&ready_->ready_storage_held(c,*frame_,held);
    }
    template<class C>bool finish(C& c,bool held){
        if(!boundary(c,held)||c.inst_count==tick_||
           !frame_->cleared_restored(c,mail_.pi_cause,mail_.pi_mask))return fail(2);
        end_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool resumed_idle(C& c,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return !error_&&stage_==2u&&cpu_==&c&&frame_&&ready_&&s&&
            c.inst_count==end_&&same_scheduler_ipc_snapshot(mail_,*s)&&
            frame_->cleared_restored(c,mail_.pi_cause,mail_.pi_mask)&&
            ready_->ready_storage_held(c,*frame_,held);
    }
private:
    const void* cpu_=nullptr;const WakeReadyWitness* ready_=nullptr;ExternalReturnWitness* frame_=nullptr;
    ColdIpcSnapshot mail_{};uint64_t tick_=0,end_=0;unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
};
}
