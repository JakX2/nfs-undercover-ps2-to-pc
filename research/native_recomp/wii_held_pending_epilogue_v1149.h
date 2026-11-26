#pragma once
#include "wii_third_alarm_suffix_v1047.h"
#include "wii_third_pending_reentry_v1067.h"
namespace undercover::wii {
struct ThirdAckNativeLabel {uint32_t pc,word,owner;bool guard;};
inline uint32_t third_ack_native_owner(std::span<const ThirdAckNativeLabel> labels,uint32_t pc,uint32_t w){
    uint32_t owner=0;unsigned hits=0;
    for(const auto& label:labels)if(label.pc==pc){
        if(++hits!=1u||label.guard||label.word!=w||!label.owner)return 0;
        owner=label.owner;
    }
    return owner;
}
struct HeldAckHelperExpectation {uint32_t pc,word;unsigned visits,entries,returns,msr;};
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
        if(stage_==8u||stage_==10u)return ack_before(c,0u,pc,w,false);
        if(stage_==6u)return dispatch_before(c,pc,w,false);
        if(stage_==4u)return same(c)&&no_si(c,w)&&next_.before(c,pc,w)?true:fail(5);
        if(stage_!=1u||!same(c)||!no_si(c,w)||c.inst_count-last_!=1u||
           !dev_->after_return_at(c.inst_count)||!frame_->saved_integer(c,expected_.context).ok())return fail(2);
        last_=c.inst_count;
        if(!held(c)||!ep_.before(c,pc,w,cause_->load(),mask_->load()))return fail(2);
        if(ep_.stage()==2u)stage_=2u;
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc){
        if(stage_==8u||stage_==10u)return same(c)&&next_.ack_entry(c,pc)?true:fail(10);
        if(stage_==6u){
            if(!same(c)||!dispatch_||!next_.dispatch_entry(c,pc)||++dispatch_entries_>5u)return fail(7);
            if(next_.stage()==6u){
                if(dispatch_entries_!=5u||dispatch_->cause_reads()!=1u||dispatch_->mask_reads()!=1u||
                   !next_.dispatch_saved(c,expected_.context)||!dispatch_->handler_ready(c,cause_->load(),mask_->load()))return fail(7);
                stage_=7u;
            }
            return true;
        }
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
        if(stage_==8u||stage_==10u)return same(c)&&next_.ack_poll(c)?PollResult::Continue:reject(10);
        if(stage_==6u)return same(c)&&dispatch_&&++dispatch_polls_<=256u&&next_.dispatch_poll(c)?PollResult::Continue:reject(8);
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
    // Only the freshly completed vector may bind the dispatcher. The
    // existing PI trace must record the actual bus results into this witness.
    template<class C>bool begin_dispatch(C& c,SiDispatchExpectations e){
        if(stage_!=5u||dispatch_||!saved(c))return fail(6);
        dispatch_.emplace(e);
        if(!next_.begin_dispatch(c,*dispatch_))return fail(6);
        stage_=6u;return true;
    }
    template<class C>bool dispatch_before(C& c,uint32_t pc,uint32_t w,bool guard){
        if(stage_!=6u||guard||!same(c)||!dispatch_||!no_si(c,w)||pc<0x80000000u||pc>0x817ffffcu||
           (pc&3u)||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w||
           ++dispatch_visits_>2048u||!next_.dispatch_tick(c))return fail(7);
        return true;
    }
    SecondSiDispatchWitness* dispatch_witness(){return dispatch_?&*dispatch_:nullptr;}
    unsigned dispatch_visits()const{return dispatch_visits_;}
    unsigned dispatch_entries()const{return dispatch_entries_;}
    unsigned dispatch_polls()const{return dispatch_polls_;}
    unsigned dispatch_reads()const{return dispatch_?dispatch_->cause_reads()+dispatch_->mask_reads():0u;}
    template<class C>bool dispatch_saved(C& c){
        return stage_==7u&&same(c)&&next_.dispatch_saved(c,expected_.context)&&
            dispatch_&&dispatch_->handler_ready(c,cause_->load(),mask_->load());
    }
    // Handoff to a distinct ACK observer on the exact third-handler
    // admission tick. Never recycle the completed transfer witness.
    template<class C>bool begin_ack(C& c,std::span<const AckCallSpan> spans,
            std::span<const AckCallEdge> edges,std::span<const AckMsrSite> msr={}){
        if(stage_!=7u||!dispatch_saved(c)||!next_.begin_ack(c,spans,edges,msr))return fail(9);
        stage_=8u;return true;
    }
    template<class C>bool ack_before(C& c,uint32_t owner,uint32_t pc,uint32_t w,bool guard){
        if((stage_!=8u&&stage_!=10u)||guard||!same(c)||++ack_visits_>2048u||!next_.ack_before(c,owner,pc,w))return fail(10);
        if(stage_==10u){
            const auto& calls=next_.ack_calls();
            if(!helper_||ack_visits_-ack_boundary_visits_>helper_->visits)return fail(14);
            const bool at_return=owner==SiDispatchWitness::Handler&&calls.depth()==0u;
            if(at_return){
                if(pc!=helper_->pc||w!=helper_->word||ack_visits_-ack_boundary_visits_!=helper_->visits||
                   calls.entries()!=helper_->entries||calls.returns()!=helper_->returns||calls.msr_writes()!=helper_->msr||
                   !next_.postack_held(c))return fail(14);
                stage_=11u;
            }else if(ack_visits_-ack_boundary_visits_==helper_->visits)return fail(14);
            return true;
        }
        if(next_.stage()==8u){
            if(!next_.ack_boundary(c))return fail(10);
            stage_=9u;
        }
        return true;
    }
    bool ack_read(SiController& ctl,unsigned off,uint32_t& v){
        return (stage_==8u||stage_==10u)&&!error_&&ctl_==&ctl&&next_.ack_read(off,v)?true:fail(11);
    }
    bool ack_write(SiController& ctl,unsigned off,uint32_t v){
        return (stage_==8u||stage_==10u)&&!error_&&ctl_==&ctl&&next_.ack_write(off,v)?true:fail(12);
    }
    template<class C>bool ack_saved(C& c){return stage_==9u&&same(c)&&next_.ack_boundary(c);}
    template<class C>bool resume_ack(C& c,uint32_t pc,uint32_t w,HeldAckHelperExpectation e){
        if(!ack_saved(c)||helper_||!e.pc||(e.pc&3u)||!e.visits||e.visits>1024u||
           e.entries<2u||e.entries>16u||e.entries!=e.returns||e.msr>4u||
           !next_.resume_ack(c,pc,w))return fail(13);
        helper_=e;ack_boundary_visits_=ack_visits_;stage_=10u;return true;
    }
    template<class C>bool helper_saved(C& c){
        return stage_==11u&&same(c)&&next_.postack_held(c);
    }
    unsigned helper_visits()const{return ack_boundary_visits_?ack_visits_-ack_boundary_visits_:0u;}
    unsigned ack_visits()const{return ack_visits_;}
    const SecondCompletionAck& completion_ack()const{return next_.completion_ack();}
    const BoundedAckCallRoute& ack_calls()const{return next_.ack_calls();}
private:
    LiveEpilogueExpectation expected_;LiveEpilogueWitness ep_;ThirdPendingReentry next_;
    std::optional<SecondSiDispatchWitness> dispatch_;
    std::optional<HeldAckHelperExpectation> helper_;unsigned ack_boundary_visits_=0;
    unsigned dispatch_visits_=0,dispatch_entries_=0,dispatch_polls_=0,ack_visits_=0;
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
