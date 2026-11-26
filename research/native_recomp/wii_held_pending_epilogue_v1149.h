#pragma once
#include "wii_third_alarm_suffix_v1047.h"
#include "wii_third_pending_reentry_v1067.h"
#include "wii_callback_identity_v796.h"
namespace undercover::wii {
struct ThirdAckNativeLabel {uint32_t pc,word,owner;bool guard;};
inline uint32_t third_ack_native_owner(std::span<const ThirdAckNativeLabel> labels,uint32_t pc,uint32_t w,bool expected_guard=false){
    uint32_t owner=0;unsigned hits=0;
    for(const auto& label:labels)if(label.pc==pc){
        if(++hits!=1u||label.guard!=expected_guard||label.word!=w||!label.owner)return 0;
        owner=label.owner;
    }
    return owner;
}
struct HeldAckHelperExpectation {uint32_t pc,word;unsigned visits,entries,returns,msr;};
struct HeldAckCallbackExpectation {uint32_t site,word;unsigned visits,ordinal;};
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
        if(stage_==8u||stage_==10u||stage_==12u)return ack_before(c,0u,pc,w,false);
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
        if(stage_==8u||stage_==10u||stage_==12u)return same(c)&&next_.ack_entry(c,pc)?true:fail(10);
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
        if(stage_==8u||stage_==10u||stage_==12u)return same(c)&&next_.ack_poll(c)?PollResult::Continue:reject(10);
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
        if((stage_!=8u&&stage_!=10u&&stage_!=12u)||guard||!same(c)||++ack_visits_>2048u)return fail(10);
        if(stage_==12u&&(!callback_||pc==callback_->site||ack_visits_-helper_boundary_visits_>=callback_->visits))return fail(16);
        if(!next_.ack_before(c,owner,pc,w))return fail(10);
        if(stage_==12u)return true;
        if(stage_==10u){
            const auto& calls=next_.ack_calls();
            if(!helper_||ack_visits_-ack_boundary_visits_>helper_->visits)return fail(14);
            const bool at_return=owner==SiDispatchWitness::Handler&&calls.depth()==0u;
            if(at_return){
                if(pc!=helper_->pc||w!=helper_->word||ack_visits_-ack_boundary_visits_!=helper_->visits||
                   calls.entries()!=helper_->entries||calls.returns()!=helper_->returns||calls.msr_writes()!=helper_->msr||
                   !next_.postack_held(c))return fail(14);
                helper_boundary_visits_=ack_visits_;stage_=11u;
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
        if(stage_==26u)return !error_&&ctl_==&ctl&&next_.handler_read(off,v)?true:fail(11);
        return (stage_==8u||stage_==10u||stage_==12u)&&!error_&&ctl_==&ctl&&next_.ack_read(off,v)?true:fail(11);
    }
    bool ack_write(SiController& ctl,unsigned off,uint32_t v){
        if(stage_==26u)return !error_&&ctl_==&ctl&&next_.handler_write(off,v)?true:fail(12);
        return (stage_==8u||stage_==10u||stage_==12u)&&!error_&&ctl_==&ctl&&next_.ack_write(off,v)?true:fail(12);
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
    template<class C>bool resume_helper(C& c,uint32_t pc,uint32_t w,HeldAckCallbackExpectation e){
        if(!helper_saved(c)||!helper_||callback_||pc!=helper_->pc||w!=helper_->word||
           e.site==pc||(e.site&3u)||e.site<0x80000000u||e.site>0x817ffffcu||
           e.word!=0x4e800421u||!e.visits||e.visits>1024u||e.ordinal!=6u||
           !next_.ack_calls().can_poll())return fail(15);
        callback_=e;stage_=12u;return true;
    }
    template<class C,std::size_t N>bool callback_frontier(C& c,uint32_t owner,uint32_t pc,uint32_t w,uint32_t target,
            const std::array<uint32_t,N>& words,const std::array<uint32_t,2>& sites){
        if(stage_!=12u||!same(c)||!callback_||!helper_||pc!=callback_->site||w!=callback_->word||
           owner!=SiDispatchWitness::Handler||++ack_visits_>2048u||ack_visits_-helper_boundary_visits_!=callback_->visits||
           c.gpr[3]>=4u||c.ctr!=target||next_.ack_calls().entries()!=helper_->entries||
           next_.ack_calls().returns()!=helper_->returns||next_.ack_calls().msr_writes()!=helper_->msr||
           classify_callback_identity(c,pc,w,callback_->ordinal,2u,target,words,sites)!=2u||
           !next_.stop_before_callback(c,owner,pc,w)||!next_.callback_boundary(c))return fail(16);
        stage_=13u;return true;
    }
    template<class C>bool callback_saved(C& c){return stage_==13u&&same(c)&&next_.callback_boundary(c);}
    // Join the previously authenticated indirect call without replaying its tick.
    template<class C,class W>bool begin_prefix(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!callback_saved(c)||!callback_||pc!=callback_->site||w!=callback_->word||
           !next_.begin_callback(c,witness,pc,w,true))return fail(17);
        prefix_=&witness;stage_=14u;return true;
    }
    template<class C,class W>bool prefix_poll(C& c,W& witness){
        return stage_==14u&&same(c)&&prefix_==&witness&&next_.callback_poll(c,witness)?true:fail(18);
    }
    template<class C,class W>bool prefix_entry(C& c,W& witness,uint32_t pc){
        return stage_==14u&&same(c)&&prefix_==&witness&&next_.callback_entry(c,witness,pc)?true:fail(18);
    }
    template<class C,class W>bool prefix_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=14u||guard||!same(c)||prefix_!=&witness||!no_si(c,w)||!next_.callback_before(c,witness,pc,w))return fail(18);
        if(witness.stage()==6u){
            if(next_.stage()!=12u||!next_.completion_ack().postack_held())return fail(18);
            stage_=15u;
        }
        return true;
    }
    template<class C,class W>bool prefix_saved(C& c,W& witness){
        return stage_==15u&&same(c)&&prefix_==&witness&&next_.callback_prefix_boundary(c,witness);
    }
    // Reuse the post-save label already charged by the prefix observer.
    template<class C,class P,class W>bool begin_prefix_time(C& c,P& prefix,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_saved(c,prefix)||time_||!no_si(c,w)||
           !next_.begin_callback_time(c,prefix,witness,pc,w))return fail(19);
        time_=&witness;stage_=16u;return true;
    }
    template<class C,class W>bool prefix_time_entry(C& c,W& witness,uint32_t pc){
        return stage_==16u&&same(c)&&time_==&witness&&next_.callback_time_entry(c,witness,pc)?true:fail(20);
    }
    template<class C,class W>bool prefix_time_poll(C& c,W& witness){
        return stage_==16u&&same(c)&&time_==&witness&&next_.callback_time_poll(c,witness)?true:fail(20);
    }
    template<class C,class W>bool prefix_time_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=16u||guard||!same(c)||time_!=&witness||!no_si(c,w)||
           !next_.callback_time_before(c,witness,pc,w))return fail(20);
        if(witness.stage()==5u){
            if(!next_.callback_time_boundary(c,witness))return fail(20);
            stage_=17u;
        }
        return true;
    }
    template<class C,class W>bool prefix_time_saved(C& c,W& witness){
        return stage_==17u&&same(c)&&time_==&witness&&next_.callback_time_boundary(c,witness);
    }
    // Classify the next original wireless call at its existing label.
    // The call instruction remains unexecuted until a separate device proof.
    template<class C,class T,class W>bool begin_prefix_frontier(C& c,T& time,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_time_saved(c,time)||frontier_||!no_si(c,w)||
           !next_.begin_callback_frontier(c,time,witness,pc,w))return fail(21);
        frontier_=&witness;stage_=witness.stage()==2u?19u:18u;
        if(stage_==19u&&!next_.callback_frontier_boundary(c,witness))return fail(21);
        return true;
    }
    template<class C,class W>bool prefix_frontier_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=18u||guard||!same(c)||frontier_!=&witness||!no_si(c,w)||
           !next_.callback_frontier_before(c,witness,pc,w))return fail(22);
        if(witness.stage()==2u){
            if(!next_.callback_frontier_boundary(c,witness))return fail(22);
            stage_=19u;
        }
        return true;
    }
    template<class C,class W>bool prefix_frontier_saved(C& c,W& witness){
        return stage_==19u&&same(c)&&frontier_==&witness&&next_.callback_frontier_boundary(c,witness);
    }
    // Only the unchanged zero-ID setter is admitted. The getter and
    // changed payload paths require their own explicit continuation.
    template<class C,class F,class W>bool begin_prefix_wireless(C& c,F& frontier,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_frontier_saved(c,frontier)||wireless_||!no_si(c,w)||
           !next_.begin_wireless(c,frontier,witness,pc,w))return fail(23);
        wireless_=&witness;stage_=20u;return true;
    }
    template<class C,class W>bool prefix_wireless_entry(C& c,W& witness,uint32_t pc){
        return stage_==20u&&same(c)&&wireless_==&witness&&next_.wireless_entry(c,witness,pc)?true:fail(24);
    }
    template<class C,class W>bool prefix_wireless_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=20u||guard||!same(c)||wireless_!=&witness||!no_si(c,w)||
           !next_.wireless_before(c,witness,pc,w))return fail(24);
        if(witness.stage()==2u){
            if(!next_.wireless_boundary(c,witness))return fail(24);
            stage_=21u;
        }
        return true;
    }
    template<class C,class W>bool prefix_wireless_saved(C& c,W& witness){
        return stage_==21u&&same(c)&&wireless_==&witness&&next_.wireless_boundary(c,witness);
    }
    template<class C,class P,class W>bool begin_prefix_suffix(C& c,P& prior,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_wireless_saved(c,prior)||suffix_||!no_si(c,w)||
           !next_.begin_callback_suffix(c,prior,witness,pc,w))return fail(25);
        suffix_=&witness;stage_=witness.stage()==2u?23u:22u;
        if(stage_==23u&&!next_.callback_suffix_boundary(c,witness))return fail(25);
        return true;
    }
    template<class C,class W>bool prefix_suffix_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=22u||guard||!same(c)||suffix_!=&witness||!no_si(c,w)||
           !next_.callback_suffix_before(c,witness,pc,w))return fail(26);
        if(witness.stage()==2u){
            if(!next_.callback_suffix_boundary(c,witness))return fail(26);
            stage_=23u;
        }
        return true;
    }
    template<class C,class W>bool prefix_suffix_poll(C& c,W& witness){
        return stage_==22u&&same(c)&&suffix_==&witness&&next_.callback_suffix_poll(c,witness)?true:fail(26);
    }
    template<class C,class W>bool prefix_suffix_saved(C& c,W& witness){
        return stage_==23u&&same(c)&&suffix_==&witness&&next_.callback_suffix_boundary(c,witness);
    }
    template<class C,class P,class W>bool begin_prefix_return(C& c,P& prior,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_suffix_saved(c,prior)||return_||!no_si(c,w)||
           !next_.begin_callback_return(c,prior,witness,pc,w))return fail(27);
        return_=&witness;stage_=24u;return true;
    }
    template<class C,class W>bool prefix_return_entry(C& c,W& witness,uint32_t pc){
        return stage_==24u&&same(c)&&return_==&witness&&next_.callback_return_entry(c,witness,pc)?true:fail(28);
    }
    template<class C,class W>bool prefix_return_poll(C& c,W& witness){
        return stage_==24u&&same(c)&&return_==&witness&&next_.callback_return_poll(c,witness)?true:fail(28);
    }
    template<class C,class W>bool prefix_return_dispatch(C& c,W& witness,uint32_t pc,uint32_t w){
        return stage_==24u&&same(c)&&return_==&witness&&no_si(c,w)&&next_.callback_return_resume(c,witness,pc,w)?true:fail(28);
    }
    template<class C,class W>bool prefix_return_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=24u||guard||!same(c)||return_!=&witness||!no_si(c,w)||
           !next_.callback_return_before(c,witness,pc,w))return fail(28);
        if(witness.stage()==5u){
            if(!next_.callback_return_boundary(c,witness))return fail(28);
            stage_=25u;
        }
        return true;
    }
    template<class C,class W>bool prefix_return_saved(C& c,W& witness){
        return stage_==25u&&same(c)&&return_==&witness&&next_.callback_return_boundary(c,witness);
    }
    // Reuse the already charged handler resume. SI status accesses are
    // admitted only by the existing third-ACK owner, never by a new token.
    template<class C,class W>bool begin_prefix_handler(C& c,W& prior,uint32_t pc,uint32_t w,
            std::span<const HandlerSuffixLabel> rows,HandlerIndexBranchExpectation index,uint32_t rd,uint32_t wr){
        if(!prefix_return_saved(c,prior)||!no_si(c,w)||
           !next_.begin_handler_suffix(c,prior,pc,w,rows,index,rd,wr))return fail(29);
        stage_=26u;return true;
    }
    template<class C>bool prefix_handler_before(C& c,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=26u||guard||!same(c)||!next_.handler_before(c,pc,w))return fail(30);
        if(next_.stage()==24u){
            if(!next_.handler_boundary(c))return fail(30);
            stage_=27u;
        }
        return true;
    }
    template<class C>bool prefix_handler_saved(C& c){
        return stage_==27u&&same(c)&&next_.handler_boundary(c);
    }
    unsigned prefix_handler_visits()const{return next_.handler_visits();}
    unsigned prefix_handler_stores()const{return next_.handler_stores();}
    unsigned prefix_handler_reads()const{return next_.handler_reads();}
    unsigned prefix_handler_writes()const{return next_.handler_writes();}
    unsigned prefix_handler_ordinal()const{return next_.handler_ordinal();}
    bool prefix_handler_taken()const{return next_.handler_taken();}
    template<class C,class W>bool begin_prefix_handler_return(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_handler_saved(c)||handler_return_||!no_si(c,w)||
           !next_.begin_handler_return(c,witness,pc,w))return fail(31);
        handler_return_=&witness;stage_=28u;return true;
    }
    template<class C,class W>bool prefix_handler_return_entry(C& c,W& witness,uint32_t pc){
        return stage_==28u&&same(c)&&handler_return_==&witness&&next_.handler_return_entry(c,witness,pc)?true:fail(32);
    }
    template<class C,class W>bool prefix_handler_return_poll(C& c,W& witness){
        return stage_==28u&&same(c)&&handler_return_==&witness&&next_.handler_return_poll(c,witness)?true:fail(32);
    }
    template<class C,class W>bool prefix_handler_return_dispatch(C& c,W& witness,uint32_t pc,uint32_t w){
        return stage_==28u&&same(c)&&handler_return_==&witness&&no_si(c,w)&&next_.handler_return_resume(c,witness,pc,w)?true:fail(32);
    }
    template<class C,class W>bool prefix_handler_return_before(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=28u||guard||!same(c)||handler_return_!=&witness||!no_si(c,w)||
           !next_.handler_return_before(c,witness,pc,w))return fail(32);
        if(witness.stage()==5u){
            if(!next_.handler_return_boundary(c,witness))return fail(32);
            stage_=29u;
        }
        return true;
    }
    template<class C,class W>bool prefix_handler_return_saved(C& c,W& witness){
        return stage_==29u&&same(c)&&handler_return_==&witness&&next_.handler_return_boundary(c,witness);
    }
    // A distinct epilogue for the now-cleared third SI interrupt.
    // The earlier pending-RFI witness cannot be recycled.
    template<class C,class W>bool begin_prefix_epilogue(C& c,W& prior,LiveEpilogueExpectation expectation,uint32_t pc,uint32_t w){
        if(!prefix_handler_return_saved(c,prior)||final_ep_||!no_si(c,w))return fail(33);
        final_ep_.emplace(expectation);
        if(!next_.begin_epilogue(c,prior,*final_ep_,pc,w))return fail(33);
        stage_=30u;return true;
    }
    template<class C>bool prefix_epilogue_before(C& c,uint32_t pc,uint32_t w,bool guard=false){
        return stage_==30u&&!guard&&same(c)&&no_si(c,w)&&next_.epilogue_before(c,pc,w)?true:fail(34);
    }
    template<class C>bool prefix_epilogue_entry(C& c,uint32_t pc){
        return stage_==30u&&same(c)&&next_.epilogue_entry(c,pc)?true:fail(34);
    }
    template<class C>bool prefix_epilogue_poll(C& c){
        if(stage_!=30u||!same(c)||!final_ep_||!next_.epilogue_poll(c))return fail(34);
        if(next_.stage()==28u)stage_=31u;
        return true;
    }
    template<class C>bool prefix_epilogue_saved(C& c)const{
        return stage_==31u&&same(c)&&final_ep_&&final_ep_->stage()==4u&&
            next_.completion_ack().postack_held_after_rfi(c.inst_count,0u);
    }
    // The first resume label is an independent terminal frontier.
    // Its two native ticks must not be charged as interrupt-handler ticks.
    template<class C>bool prefix_resume_dispatch(C& c,uint32_t pc){
        if(stage_!=31u||!same(c)||!final_ep_||!next_.epilogue_resume_dispatch(c,pc))return fail(35);
        stage_=32u;return true;
    }
    template<class C>bool prefix_resume_label(C& c,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=32u||guard||!same(c)||!final_ep_||!next_.epilogue_resume_label(c,pc,w))return fail(36);
        stage_=33u;return true;
    }
    template<class C>bool prefix_resume_saved(C& c)const{
        return stage_==33u&&same(c)&&final_ep_&&final_ep_->stage()==5u&&
            next_.completion_ack().postack_held_after_rfi(c.inst_count,2u);
    }
    template<class C,class W>bool begin_prefix_leaf(C& c,W& witness,uint32_t pc,uint32_t w){
        if(!prefix_resume_saved(c)||leaf_||!next_.begin_resume_leaf(c,witness,pc,w))return fail(37);
        leaf_=&witness;stage_=34u;return true;
    }
    template<class C,class W>bool prefix_leaf_blr(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        return stage_==34u&&!guard&&same(c)&&leaf_==&witness&&next_.resume_leaf_blr(c,witness,pc,w)?true:fail(38);
    }
    template<class C,class W>bool prefix_leaf_poll(C& c,W& witness){
        return stage_==34u&&same(c)&&leaf_==&witness&&next_.resume_leaf_poll(c,witness)?true:fail(38);
    }
    template<class C,class W>bool prefix_leaf_dispatch(C& c,W& witness,uint32_t pc){
        return stage_==34u&&same(c)&&leaf_==&witness&&next_.resume_leaf_dispatch(c,witness,pc)?true:fail(38);
    }
    template<class C,class W>bool prefix_leaf_return(C& c,W& witness,uint32_t pc,uint32_t w,bool guard=false){
        if(stage_!=34u||guard||!same(c)||leaf_!=&witness||!next_.resume_leaf_return(c,witness,pc,w))return fail(38);
        stage_=35u;return true;
    }
    template<class C,class W>bool prefix_leaf_saved(C& c,W& witness)const{
        return stage_==35u&&same(c)&&leaf_==&witness&&next_.resume_leaf_saved(c,witness);
    }
    unsigned prefix_epilogue_visits()const{return final_ep_?final_ep_->visits():0u;}
    unsigned prefix_epilogue_failure()const{return final_ep_?final_ep_->failure():0u;}
    unsigned callback_visits()const{return helper_boundary_visits_?ack_visits_-helper_boundary_visits_:0u;}
    unsigned helper_visits()const{return ack_boundary_visits_?(helper_boundary_visits_?helper_boundary_visits_:ack_visits_)-ack_boundary_visits_:0u;}
    unsigned ack_visits()const{return ack_visits_;}
    const SecondCompletionAck& completion_ack()const{return next_.completion_ack();}
    const BoundedAckCallRoute& ack_calls()const{return next_.ack_calls();}
private:
    LiveEpilogueExpectation expected_;LiveEpilogueWitness ep_;ThirdPendingReentry next_;
    std::optional<SecondSiDispatchWitness> dispatch_;
    std::optional<LiveEpilogueWitness> final_ep_;
    std::optional<HeldAckHelperExpectation> helper_;std::optional<HeldAckCallbackExpectation> callback_;
    const void* prefix_=nullptr;const void* time_=nullptr;const void* frontier_=nullptr;const void* wireless_=nullptr;const void* suffix_=nullptr;const void* return_=nullptr;const void* handler_return_=nullptr;const void* leaf_=nullptr;
    unsigned ack_boundary_visits_=0,helper_boundary_visits_=0;
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
