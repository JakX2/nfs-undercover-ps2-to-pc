#pragma once
#include "wii_second_completion_ack_v950.h"
#include "wii_external_return_v706.h"
#include "v958_private_second_ack.h"
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
inline bool time_enabled(){const char* v=std::getenv("UNDERCOVER_V975_SECOND_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool post_enabled(){const char* v=std::getenv("UNDERCOVER_V967_POST_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V958_SECOND_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return ack.stage()!=0u;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V958_ACK_INVALID kind="<<kind<<" stage="<<ack.stage()<<" reason="<<ack.failure()
             <<" call_reason="<<calls.failure()<<" visits="<<visits<<std::endl;std::_Exit(126);
}
template<class C>bool start(C& c,ExternalReturnWitness& captured){
    if(frame||active()||!captured.saved_integer(c,context).ok())return false;
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
    if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
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
#ifdef UNDERCOVER_V975_PRIVATE_TIME
    if(time_enabled()&&post_seen&&pc==time_call){
        if(time_tick||calls.depth()!=1u||!ack.postack_held())reject(10);
        time_tick=visits;time_entries=calls.entries();time_returns=calls.returns();time_msr=calls.msr_writes();
    }
    if(time_enabled()&&time_tick&&pc==time_call+4u){
        if(calls.depth()!=0u||calls.entries()-time_entries!=4u||calls.returns()-time_returns!=4u||
           calls.msr_writes()-time_msr!=2u||!ack.postack_held()||visits<=time_tick)reject(10);
        std::cout<<std::dec<<"V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits="
                 <<visits-time_tick<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
    if(post_seen)return;
#endif
    if(ack.stage()==4u&&pc>=spans[0].root&&pc<spans[0].end&&calls.depth()==0u){
        if(!post_visits||visits<=post_visits||calls.returns()<=post_returns||!ack.postack_held())reject(9);
        std::cout<<std::dec<<"V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits="
                 <<visits-post_visits<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V975_PRIVATE_TIME
        if(time_enabled()){post_seen=true;return;}
#endif
        std::_Exit(0);
    }
}
template<class C>bool poll(C& c){
    if(!frame||!frame->saved_integer(c,context).ok()||!calls.can_poll()||!ack.poll(c.inst_count))reject(3);
    return false;
}
template<class C>void observe(uint32_t pc,C& c){
    if(!frame||!frame->saved_integer(c,context).ok()||!calls.entry(c,pc)||!ack.poll(c.inst_count))reject(4);
}
}
