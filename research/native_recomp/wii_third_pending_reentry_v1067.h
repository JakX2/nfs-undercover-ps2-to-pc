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
        if(!ack_frame(c))return fail(11);
        if(ack_read_reg_<32u){
            if(!ack_read_result_||c.gpr[ack_read_reg_]!=*ack_read_result_)return fail(16);
            ack_read_reg_=32u;ack_read_result_.reset();
        }
        if(!ack_.before(c,pc,w,true)||!ack_calls_.before(c,pc,w,owner))return fail(11);
        if(ack_.stage()==3u){
            if(ack_.token()!=3u||!ack_.reads()||!ack_.writes()||!ack_calls_.entries()||
               !ack_calls_.returns()||!ack_.response_class_verified())return fail(11);
            stage_=8u;ack_successor_=pc;ack_successor_word_=w;return true;
        }
        observe_ack_access(c,w);
        return true;
    }
    // Resume the exact verified successor, at the same tick. The native
    // call witness already consumed its label; never consume it twice.
    template<class C>bool resume_ack(C& c,uint32_t pc,uint32_t w){
        if(stage_!=8u||error_||cpu_!=&c||!dev_||dev_->stage()!=3u||
           pc!=ack_successor_||w!=ack_successor_word_||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !ack_.resume_after_ack(c,pc,w))return fail(17);
        stage_=9u;observe_ack_access(c,w);return true;
    }
private:
    template<class C>void observe_ack_access(C& c,uint32_t w){
        const auto access=PostAckTransferDevice::word_access(c,w);
        if(access.kind==PostAckTransferDevice::Access::Read&&PostAckTransferDevice::offset(access.address)){
            ack_read_reg_=(w>>21)&31u;ack_read_reverse_=(w>>26)==31u&&((w>>1)&1023u)==534u;
        }
    }
public:
    template<class C>bool ack_entry(C& c,uint32_t pc){
        return ack_frame(c)&&ack_calls_.entry(c,pc)&&ack_.poll(c.inst_count)?true:fail(12);
    }
    template<class C>bool ack_poll(C& c){
        return ack_frame(c)&&ack_calls_.can_poll()&&ack_.poll(c.inst_count)?true:fail(13);
    }
    bool ack_read(unsigned off,uint32_t& v){
        if(!ack_active()||error_||ack_read_reg_>=32u||ack_read_result_||!ack_.read(*ctl_,off,v))return fail(14);
        // The hardware read is always the bus value. Only the original
        // translated lwbrx instruction reverses it in the destination GPR.
        ack_read_result_=ack_read_reverse_?(v>>24)|((v>>8)&0xff00u)|((v<<8)&0xff0000u)|(v<<24):v;
        return true;
    }
    bool ack_write(unsigned off,uint32_t v){
        return ack_active()&&!error_&&ack_.write(*ctl_,off,v)?true:fail(15);
    }
    // Observe the original alternate indirect-call frontier without executing it.
    template<class C>bool stop_before_callback(C& c,uint32_t owner,uint32_t pc,uint32_t w){
        if(stage_!=9u||!ack_frame(c)||owner!=SiDispatchWitness::Handler||ack_read_reg_!=32u||
           w!=0x4e800421u||!ack_.before(c,pc,w,true)||!ack_.postack_held()||
           !ack_calls_.stop_before_indirect(c,pc,w))return fail(18);
        callback_site_=pc;callback_word_=w;stage_=10u;return true;
    }
    // A fresh callback witness takes over the exact unexecuted indirect
    // call. The cleared third ACK retains exclusive device ownership.
    template<class C,class W>bool begin_callback(C& c,W& witness,uint32_t pc,uint32_t w,bool identity){
        if(stage_!=10u||error_||cpu_!=&c||dev_->stage()!=3u||!identity||
           pc!=callback_site_||w!=callback_word_||!ack_.postack_held()||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !witness.start_dispatch(c,pc,w,true,true))return fail(19);
        callback_=&witness;callback_channel_=c.gpr[3];stage_=11u;return true;
    }
    template<class C,class W>bool callback_poll(C& c,W& witness){
        return callback_frame(c,witness)&&ack_.poll(c.inst_count)&&ack_.postack_held()&&
               witness.dispatch_poll(c,true)?true:fail(20);
    }
    template<class C,class W>bool callback_entry(C& c,W& witness,uint32_t pc){
        return callback_frame(c,witness)&&(witness.stage()!=1u||ack_.accept_dispatch_tick(c))&&
               ack_.postack_held()&&witness.entry(c,pc,true)?true:fail(21);
    }
    template<class C,class W>bool callback_before(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!callback_frame(c,witness)||!ack_.before(c,pc,w,true)||!ack_.postack_held()||
           !witness.before(c,pc,w,true))return fail(22);
        if(witness.stage()==6u){callback_resume_=pc;callback_resume_word_=w;stage_=12u;}
        return true;
    }
    // The exact resume label was consumed by the fresh ACK and prefix
    // witness. Transfer to a new time witness without replaying that tick.
    template<class C,class P,class W>bool begin_callback_time(C& c,P& prefix,W& witness,uint32_t pc,uint32_t w){
        if(stage_!=12u||error_||cpu_!=&c||callback_!=&prefix||prefix.stage()!=6u||
           pc!=callback_resume_||w!=callback_resume_word_||pc!=prefix.resume()||time_||
           !dev_||dev_->stage()!=3u||!ack_.poll(c.inst_count)||!ack_.postack_held()||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !witness.start(c,pc,w,true,true)||!witness.before(c,pc,w,true))return fail(23);
        time_=&witness;stage_=13u;return true;
    }
    template<class C,class W>bool callback_time_before(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!time_frame(c,witness)||!ack_.before(c,pc,w,true)||!ack_.postack_held()||
           !witness.before(c,pc,w,true))return fail(24);
        if(witness.stage()==5u){time_resume_=pc;time_word_=w;stage_=14u;}
        return true;
    }
    template<class C,class W>bool callback_time_entry(C& c,W& witness,uint32_t pc){
        return time_frame(c,witness)&&ack_.poll(c.inst_count)&&ack_.postack_held()&&
               witness.entry(c,pc,true)?true:fail(25);
    }
    template<class C,class W>bool callback_time_poll(C& c,W& witness){
        return time_frame(c,witness)&&ack_.poll(c.inst_count)&&ack_.postack_held()&&
               witness.poll(c,true)?true:fail(26);
    }
    // No new device ownership or tick at the authenticated time return.
    template<class C,class T,class W>bool begin_callback_frontier(C& c,T& time,W& witness,uint32_t pc,uint32_t w){
        if(stage_!=14u||error_||cpu_!=&c||time_!=&time||time.stage()!=5u||frontier_||
           pc!=time_resume_||w!=time_word_||callback_channel_>=4u||!dev_||dev_->stage()!=3u||
           !ack_.poll(c.inst_count)||!ack_.postack_held()||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !witness.start(c,pc,w,callback_channel_,true,true)||!witness.before(c,pc,w,true))return fail(27);
        frontier_=&witness;stage_=witness.stage()==2u?16u:15u;
        if(stage_==16u){frontier_site_=pc;frontier_word_=w;}return true;
    }
    template<class C,class W>bool callback_frontier_before(C& c,W& witness,uint32_t pc,uint32_t w){
        if(stage_!=15u||error_||cpu_!=&c||frontier_!=&witness||!dev_||dev_->stage()!=3u||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !ack_.before(c,pc,w,true)||!ack_.postack_held()||!witness.before(c,pc,w,true))return fail(28);
        if(witness.stage()==2u){frontier_site_=pc;frontier_word_=w;stage_=16u;}
        return true;
    }
    // Admit only the observed unchanged setter lane. A changed payload
    // would require its own EXI transaction and exclusive device proof.
    template<class C,class F,class W>bool begin_wireless(C& c,F& frontier,W& witness,uint32_t pc,uint32_t w){
        if(stage_!=16u||error_||cpu_!=&c||frontier_!=&frontier||wireless_||
           frontier.stage()!=2u||frontier.ordinal()!=3u||frontier.zero_id()!=1u||
           pc!=frontier_site_||w!=frontier_word_||c.gpr[3]!=callback_channel_||c.gpr[4]!=0u||
           !dev_||dev_->stage()!=3u||!ack_.poll(c.inst_count)||!ack_.postack_held()||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !witness.start(c,pc,w,true,true)||witness.changed()||witness.ordinal()!=3u)return fail(29);
        wireless_=&witness;stage_=17u;return true;
    }
    template<class C,class W>bool wireless_before(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!wireless_frame(c,witness)||!ack_.before(c,pc,w,true)||!ack_.postack_held()||
           !witness.before(c,pc,w,true))return fail(30);
        if(witness.stage()==2u){wireless_resume_=pc;wireless_word_=w;stage_=18u;}
        return true;
    }
    template<class C,class W>bool wireless_entry(C& c,W& witness,uint32_t pc){
        return wireless_frame(c,witness)&&ack_.poll(c.inst_count)&&ack_.postack_held()&&
               witness.entry(c,pc,true)&&witness.stage()==1u?true:fail(31);
    }
    template<class C,class P,class W>bool begin_callback_suffix(C& c,P& prior,W& witness,uint32_t pc,uint32_t w){
        if(stage_!=18u||error_||cpu_!=&c||wireless_!=&prior||suffix_||prior.stage()!=2u||prior.changed()||
           pc!=wireless_resume_||w!=wireless_word_||!dev_||dev_->stage()!=3u||
           !ack_.poll(c.inst_count)||!ack_.postack_held()||
           !next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok()||
           !witness.start(c,pc,w,true,true)||!witness.before(c,pc,w,true))return fail(32);
        suffix_=&witness;stage_=witness.stage()==2u?20u:19u;
        if(stage_==20u){suffix_site_=pc;suffix_word_=w;}return true;
    }
    template<class C,class W>bool callback_suffix_before(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!suffix_frame(c,witness)||!ack_.before(c,pc,w,true)||!ack_.postack_held()||
           !witness.before(c,pc,w,true))return fail(33);
        if(witness.stage()==2u){suffix_site_=pc;suffix_word_=w;stage_=20u;}
        return true;
    }
    template<class C,class W>bool callback_suffix_poll(C& c,W& witness){
        return suffix_frame(c,witness)&&ack_.poll(c.inst_count)&&ack_.postack_held()&&
               witness.poll(c,true)?true:fail(34);
    }
    bool ack_active()const{return stage_==7u||stage_==9u;}
    template<class C>bool postack_held(C& c)const{
        return stage_==9u&&ack_frame(c)&&ack_read_reg_==32u&&ack_.postack_held();
    }
    const SecondCompletionAck& completion_ack()const{return ack_;}
    const BoundedAckCallRoute& ack_calls()const{return ack_calls_;}
private:
    template<class C>bool ack_frame(C& c)const{
        return ack_active()&&!error_&&cpu_==&c&&dev_&&dev_->stage()==3u&&
               next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok();
    }
    template<class C,class W>bool callback_frame(C& c,W& witness)const{
        return stage_==11u&&!error_&&cpu_==&c&&callback_==&witness&&dev_&&dev_->stage()==3u&&
               next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok();
    }
    template<class C,class W>bool time_frame(C& c,W& witness)const{
        return stage_==13u&&!error_&&cpu_==&c&&time_==&witness&&dev_&&dev_->stage()==3u&&
               next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok();
    }
    template<class C,class W>bool wireless_frame(C& c,W& witness)const{
        return stage_==17u&&!error_&&cpu_==&c&&wireless_==&witness&&dev_&&dev_->stage()==3u&&
               next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok();
    }
    template<class C,class W>bool suffix_frame(C& c,W& witness)const{
        return stage_==19u&&!error_&&cpu_==&c&&suffix_==&witness&&dev_&&dev_->stage()==3u&&
               next_.captured().saved_integer(c,SiDispatchWitness::Thread).ok();
    }
    const void* suffix_=nullptr;
    uint32_t suffix_site_=0,suffix_word_=0;
    const void* wireless_=nullptr;
    uint32_t frontier_site_=0,frontier_word_=0,wireless_resume_=0,wireless_word_=0;
    const void* time_=nullptr;const void* frontier_=nullptr;
    uint32_t time_resume_=0,time_word_=0,callback_channel_=4u;
    uint32_t callback_resume_=0,callback_resume_word_=0;
    const void* callback_=nullptr;
    uint32_t callback_site_=0,callback_word_=0,ack_successor_=0,ack_successor_word_=0;
    unsigned ack_read_reg_=32u;bool ack_read_reverse_=false;
    std::optional<uint32_t> ack_read_result_;
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
