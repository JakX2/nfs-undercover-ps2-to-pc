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
inline thread_local unsigned visits=0;
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V958_SECOND_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return ack.stage()!=0u;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V958_ACK_INVALID kind="<<kind<<" stage="<<ack.stage()<<" reason="<<ack.failure()
             <<" call_reason="<<calls.failure()<<" visits="<<visits<<std::endl;std::_Exit(126);
}
template<class C>bool start(C& c,ExternalReturnWitness& captured){
    if(frame||active()||!captured.saved_integer(c,context).ok()||!calls.begin(c,spans,edges))return false;
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
