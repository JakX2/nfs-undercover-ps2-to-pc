#pragma once
#include "wii_si_handler_time_v742.h"
#include "v742_private_time_expectations.h"
#include "v709_private_os_leaf_expectations.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v742 {
inline thread_local SiHandlerTime route(expected,v709::expected_leaves);
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V742_HANDLER_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
[[noreturn]]inline void reject(){
    std::cout<<"V742_TIME_INVALID reason="<<route.failure()<<" stage="<<route.stage()
             <<" leaf="<<route.cursor()+1<<" witness="<<route.leaf_failure()<<" trace="<<si_completion_ack_trace.failure()<<std::endl;std::_Exit(126);
}
inline void event(unsigned n){std::cout<<"V742_TIME_STAGE n="<<n<<std::endl;}
inline void leaf_event(unsigned ordinal,unsigned n){std::cout<<"V742_TIME_LEAF ordinal="<<ordinal<<" n="<<n<<std::endl;}
inline bool eligible(uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    return enabled()&&route.stage()==0&&pc==expected.site&&w==expected.branch&&ordinal==3&&kind==1;
}
template<class C>void start(C& c,uint32_t pc,uint32_t w){
    if(!route.start(c,pc,w,si_completion_ack_trace))reject();
    event(1);
}
template<class C>bool observe(uint32_t a,C& c){
    if(!route.active())return false;
    bool leaf=route.leaf_active();
    if(!route.entry(a,c,si_completion_ack_trace))reject();
    if(leaf)leaf_event(route.cursor()+1,2);else event(2);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    unsigned old=route.cursor();
    if(!route.before(c,pc,w,ordinal,kind,si_completion_ack_trace))reject();
    if(route.cursor()!=old)leaf_event(old+1,3);
    if(route.leaf_active())leaf_event(route.cursor()+1,1);
}
template<class C>void leaf_before(C& c,uint32_t pc,uint32_t w,unsigned ordinal){
    if(!route.leaf_before(c,pc,w,ordinal,si_completion_ack_trace))reject();
}
template<class C>bool poll(C& c){
    if(!route.poll(c,si_completion_ack_trace))reject();
    return false;
}
template<class C>void returned(C& c,uint32_t pc){
    if(!route.returned(c,pc,si_completion_ack_trace))reject();
    event(3);
}
}
