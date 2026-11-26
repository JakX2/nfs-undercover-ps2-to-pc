#pragma once
#include "wii_second_completion_ack_v950.h"
#include "wii_external_return_v706.h"
#include "v958_private_second_ack.h"
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
#include "wii_si_transfer_arguments_v981.h"
#endif
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
#include "wii_callback_identity_v796.h"
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
#include "wii_callback_prefix_v800.h"
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
#include "v813_private_callback_time.h"
#endif
#endif
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v958 {
inline thread_local SecondCompletionAck ack;
inline thread_local BoundedAckCallRoute calls;
inline thread_local ExternalReturnWitness* frame=nullptr;
inline thread_local unsigned visits=0,post_visits=0,post_returns=0;
#ifdef UNDERCOVER_V975_PRIVATE_TIME
inline thread_local unsigned time_tick=0,time_entries=0,time_returns=0,time_msr=0;
inline thread_local bool post_seen=false;
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
inline thread_local unsigned shared_tick=0,shared_entries=0,shared_returns=0,shared_msr=0;
inline thread_local bool shared_seen=false;
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
inline thread_local unsigned helper_return_visits=0;
inline thread_local bool error_helper_seen=false;
inline bool error_frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V1021_ERROR_FRONTIER");return v&&v[0]=='1'&&v[1]=='\0';}
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
inline thread_local CallbackPrefixWitness<second_callback_prefix.size(),second_callback_save.size()> callback_prefix(transfer_callback,second_callback_save_root,second_callback_prefix,second_callback_save);
inline bool callback_enabled(){const char* v=std::getenv("UNDERCOVER_V1009_SECOND_CALLBACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool prefix_active(){return callback_prefix.stage()>=1u&&callback_prefix.stage()<=5u;}
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
inline thread_local CallbackTimeWitness callback_time(v813::expected);
inline bool callback_time_enabled(){const char* v=std::getenv("UNDERCOVER_V1014_SECOND_CALLBACK_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool callback_time_active(){return callback_time.stage()>=1u&&callback_time.stage()<=4u;}
#endif
inline bool callback_active(){
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active())return true;
#endif
    return prefix_active();
}
#endif
inline bool success_frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V995_SUCCESS_FRONTIER");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool shared_enabled(){const char* v=std::getenv("UNDERCOVER_V989_SHARED_COMPLETION");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool error_completion_enabled(){const char* v=std::getenv("UNDERCOVER_V1015_ERROR_COMPLETION");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
inline thread_local bool time_seen=false;
inline thread_local unsigned time_return_visits=0;
inline bool frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V981_SECOND_FRONTIER");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool time_enabled(){const char* v=std::getenv("UNDERCOVER_V975_SECOND_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool post_enabled(){const char* v=std::getenv("UNDERCOVER_V967_POST_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V958_SECOND_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return ack.stage()!=0u;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V958_ACK_INVALID kind="<<kind<<" stage="<<ack.stage()<<" reason="<<ack.failure()
             <<" call_reason="<<calls.failure()<<" visits="<<visits<<std::endl;std::_Exit(126);
}
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
// Distinguish the three fail-closed shared-time checks without exposing
// guest addresses, register values, original words, or raw traces.
[[noreturn]]inline void reject_shared(unsigned phase){
    const bool started=shared_tick!=0u;
    std::cout<<std::dec<<"V989_SHARED_DETAIL phase="<<phase<<" depth="<<calls.depth()
             <<" started="<<started<<" seen="<<shared_seen<<" post="<<post_seen
             <<" held="<<ack.postack_held()<<" entries="<<calls.entries()-(started?shared_entries:0u)
             <<" returns="<<calls.returns()-(started?shared_returns:0u)
             <<" msr="<<calls.msr_writes()-(started?shared_msr:0u)
             <<" visits="<<visits<<std::endl;
    reject(12);
}
#endif
template<class C>bool start(C& c,ExternalReturnWitness& captured){
    if(frame||active()||!captured.saved_integer(c,context).ok())return false;
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(callback_enabled()&&!success_frontier_enabled())return false;
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_enabled()&&!callback_enabled())return false;
#endif
#endif
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
    if(success_frontier_enabled()&&(!shared_enabled()||!time_enabled()||!frontier_enabled()||!post_enabled()))return false;
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(frontier_enabled()&&(!time_enabled()||!post_enabled()))return false;
#endif
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
    if(error_completion_enabled()&&!shared_enabled())return false;
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
    if(error_frontier_enabled()&&(!error_completion_enabled()||!success_frontier_enabled()||!time_enabled()||!frontier_enabled()))return false;
    if(error_completion_enabled()&&time_enabled()&&!error_frontier_enabled())return false;
#else
    if(error_completion_enabled()&&time_enabled())return false;
#endif
    if(shared_enabled()){
        if(!post_enabled()||!calls.begin(c,time_spans,shared_edges,msr_sites))return false;
    }else
#endif
#ifdef UNDERCOVER_V975_PRIVATE_TIME
    if(time_enabled()){
        if(!post_enabled()||!calls.begin(c,time_spans,time_edges,msr_sites))return false;
    }else
#endif
    if(!calls.begin(c,spans,edges))return false;
    frame=&captured;return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w,bool guard){
    if(!active())return;
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active()){
        if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !ack.before(c,pc,w,true)||!ack.postack_held()||!callback_time.before(c,pc,w,true))reject(15);
        if(callback_time.stage()==5u){
            std::cout<<std::dec<<"V1014_CALLBACK_TIME original_return=1 leaves="<<callback_time.cursor()
                     <<" system_visits="<<callback_time.time_visits()<<" leaf_visits="<<callback_time.leaf_visits()
                     <<" polls="<<callback_time.polls()<<" reads="<<callback_time.reads()
                     <<" offset=1 token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(prefix_active()){
        if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !ack.before(c,pc,w,true)||!ack.postack_held()||!callback_prefix.before(c,pc,w,true))reject(14);
        if(callback_prefix.stage()==6u){
            std::cout<<std::dec<<"V1009_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes="<<callback_prefix.writes()
                     <<" visits="<<callback_prefix.visits()<<" token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
            if(callback_time_enabled()){
                // Prefix already consumed this native label and SI tick.
                if(!callback_time.start(c,pc,w,ack.postack_held(),true)||
                   !callback_time.before(c,pc,w,ack.postack_held()))reject(15);
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
    if(success_frontier_enabled()&&pc==success_callback_sites[0]){
        if(!guard||(!shared_seen&&!error_helper_seen)||!post_seen||!helper_return_visits||time_seen||w!=0x4e800421u||
           !frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !ack.before(c,pc,w,true)||!ack.postack_held()||!calls.stop_before_indirect(c,pc,w))reject(13);
        if(error_frontier_enabled()){
            if(!error_helper_seen||!ack.no_response_verified()||shared_seen||shared_tick||
               visits-helper_return_visits!=71u)reject(16);
            std::cout<<"V1021_ERROR_FRONTIER branch=6 visits=71 handler_time=0 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
        }
        const auto category=classify_callback_identity(c,pc,w,6u,2u,transfer_callback,success_callback_words,success_callback_sites);
        std::cout<<std::dec<<"V995_CALLBACK_FRONTIER target_class="<<category<<" aligned="<<(!(c.ctr&3u))
                 <<" visits="<<visits-helper_return_visits<<" token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
        if(callback_enabled()&&category==2u&&c.ctr==transfer_callback){
            if(c.gpr[3]>=4u||!callback_prefix.start_dispatch(c,pc,w,true,true))reject(14);
            return;
        }
#endif
        std::_Exit(0);
    }
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(frontier_enabled()&&time_seen&&pc==transfer_call){
        if(!guard||w!=transfer_branch||!frame||!frame->saved_integer(c,context).ok()||
           ++visits>8192u||!ack.before(c,pc,w,true)||!ack.postack_held()||!calls.stop_before_direct(c,pc,w))reject(11);
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
        if(error_frontier_enabled()){
            if(!error_helper_seen||!ack.no_response_verified()||shared_seen||shared_tick||
               visits-helper_return_visits!=78u)reject(16);
            std::cout<<"V1021_ERROR_FRONTIER branch=4 visits=78 handler_time=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
        }
#endif
        const auto a=inspect_si_transfer_arguments(c,transfer_data,transfer_slots,transfer_callback);
        std::cout<<std::dec<<"V981_TRANSFER_FRONTIER type="<<a.type<<" idle="<<a.idle<<" queue_match="<<a.queue_match
            <<" callback_known="<<a.callback_known<<" admitted="<<a.admitted()<<" visits="<<visits-time_return_visits
            <<" token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
#endif
    if(guard||!frame||!frame->saved_integer(c,context).ok()){
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
        if(shared_enabled())std::cout<<std::dec<<"V989_SHARED_REFUSAL guard="<<guard<<" frame="<<bool(frame&&frame->saved_integer(c,context).ok())<<" depth="<<calls.depth()<<" visits="<<visits<<std::endl;
#endif
        reject(1);
    }
    if(++visits>8192u||
       !ack.before(c,pc,w,true)||!calls.before(c,pc,w))reject(1);
    if(ack.stage()==3u){
        if(ack.token()<2u||!ack.reads()||!ack.writes()||calls.entries()<2u||!calls.returns())reject(2);
        std::cout<<std::dec<<"V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits="
                 <<visits<<" reads="<<ack.reads()<<" writes="<<ack.writes()<<" boot_verified=0"<<std::endl;
        if(!post_enabled())std::_Exit(0);
        post_visits=visits;post_returns=calls.returns();
        if(!ack.resume_after_ack(c,pc,w))reject(9);
        return;
    }
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
    if(shared_enabled()&&pc==completion_time_call){
        if(shared_tick||post_seen||ack.stage()!=4u||calls.depth()!=2u||!ack.postack_held())reject_shared(1);
        shared_tick=visits;shared_entries=calls.entries();shared_returns=calls.returns();shared_msr=calls.msr_writes();
    }
    if(shared_enabled()&&shared_tick&&pc==completion_time_call+4u){
        if(shared_seen||calls.depth()!=1u||calls.entries()-shared_entries!=4u||calls.returns()-shared_returns!=4u||
           calls.msr_writes()-shared_msr!=2u||!ack.postack_held()||visits<=shared_tick)reject_shared(2);
        shared_seen=true;
        std::cout<<std::dec<<"V989_SHARED_TIME_RESULT original_time=1 leaves=3 unchanged_msr=2 visits="<<visits-shared_tick
                 <<" token_preserved=1 saved_fields=38 boot_verified=0"<<std::endl;
    }
#endif
#ifdef UNDERCOVER_V975_PRIVATE_TIME
    if(time_enabled()&&post_seen&&pc==time_call){
        if(time_tick||calls.depth()!=1u||!ack.postack_held())reject(10);
        time_tick=visits;time_entries=calls.entries();time_returns=calls.returns();time_msr=calls.msr_writes();
    }
    if(time_enabled()&&time_tick&&pc==time_call+4u){
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
        if(time_seen)reject(11);
#endif
        if(calls.depth()!=0u||calls.entries()-time_entries!=4u||calls.returns()-time_returns!=4u||
           calls.msr_writes()-time_msr!=2u||!ack.postack_held()||visits<=time_tick)reject(10);
        std::cout<<std::dec<<"V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits="
                 <<visits-time_tick<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
        if(frontier_enabled()){time_seen=true;time_return_visits=visits;return;}
#endif
        std::_Exit(0);
    }
    if(post_seen)return;
#endif
    if(ack.stage()==4u&&pc>=spans[0].root&&pc<spans[0].end&&calls.depth()==0u){
        if(!post_visits||visits<=post_visits||calls.returns()<=post_returns||!ack.postack_held())reject(9);
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
        if(shared_enabled()&&!shared_seen){
            // V1013: 32 original no-response returns, never a waiver
            // of the successful-response timing-call requirement.
            if(!error_completion_enabled()||!ack.no_response_verified()||
               shared_tick||calls.entries()!=6u||calls.returns()!=6u||
               calls.msr_writes()!=2u||visits-post_visits!=130u)reject_shared(3);
            std::cout<<std::dec<<"V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits="
                     <<visits-post_visits<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
            std::cout<<"V1015_ERROR_HELPER_RETURN original_helper_return=1 no_response=1 shared_time=0 entries=6 returns=6 msr=2 visits=130 token_preserved=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
            if(error_frontier_enabled()){
                error_helper_seen=true;helper_return_visits=visits;post_seen=true;return;
            }
#endif
            std::_Exit(0);
        }
        if(error_completion_enabled()&&ack.no_response_verified())reject_shared(3);
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
        if(error_frontier_enabled())reject(16);
#endif
#endif
        std::cout<<std::dec<<"V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits="
                 <<visits-post_visits<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V975_PRIVATE_TIME
        if(time_enabled()){
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
            if(success_frontier_enabled())helper_return_visits=visits;
#endif
            post_seen=true;return;
        }
#endif
        std::_Exit(0);
    }
}
template<class C>bool poll(C& c){
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!ack.postack_held()||!callback_time.poll(c,true))reject(15);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(prefix_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!ack.postack_held()||!callback_prefix.dispatch_poll(c,true))reject(14);
        return false;
    }
#endif
    if(!frame||!frame->saved_integer(c,context).ok()||!calls.can_poll()||!ack.poll(c.inst_count))reject(3);
    return false;
}
template<class C>void observe(uint32_t pc,C& c){
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!ack.postack_held()||!callback_time.entry(c,pc,true))reject(15);
        return;
    }
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(prefix_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||(callback_prefix.stage()==1u&&!ack.accept_dispatch_tick(c))||
           !ack.postack_held()||!callback_prefix.entry(c,pc,true))reject(14);
        return;
    }
#endif
    if(!frame||!frame->saved_integer(c,context).ok()||!calls.entry(c,pc)||!ack.poll(c.inst_count))reject(4);
}
}
