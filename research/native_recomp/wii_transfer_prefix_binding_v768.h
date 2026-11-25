#pragma once
#include "v768_private_transfer_prefix.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v768 {
inline thread_local TransferPrefixWitness route(expected);
inline bool active(){return route.stage()!=0;}
inline bool eligible(uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    const char* v=std::getenv("UNDERCOVER_V768_TRANSFER_PREFIX");
    return v&&v[0]=='1'&&v[1]=='\0'&&!active()&&pc==expected.site&&w==expected.branch&&ordinal==4&&kind==1;
}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V768_TRANSFER_INVALID kind="<<kind<<" reason="<<route.failure()<<" stage="<<route.stage()<<" visits="<<route.visits()<<" trace="<<si_completion_ack_trace.failure()<<std::endl;std::_Exit(126);
}
template<class C>void start(C& c,uint32_t pc,uint32_t w){
    if(!route.start(c,pc,w,si_completion_ack_trace))reject(1);
    std::cout<<std::dec<<"V768_TRANSFER_ENTRY channel="<<route.channel()<<" type="<<unsigned(route.type())<<" idle="<<unsigned(route.idle())<<std::endl;
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    if(!route.entry(c,pc,si_completion_ack_trace))reject(2);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!route.before(c,pc,w,si_completion_ack_trace))reject(3);
    if(route.stage()==3){
        std::cout<<std::dec<<"V768_TRANSFER_RESULT original_entry=1 save="<<route.save_done()<<" disable="<<route.disable_done()<<" boundary="<<route.stop()<<" visits="<<route.visits()<<" mmio_executed=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
template<class C>void save_before(C& c,uint32_t pc,uint32_t w){
    if(active()&&!route.save_before(c,pc,w,si_completion_ack_trace))reject(4);
}
template<class C>void disable_before(C& c,uint32_t pc,uint32_t w,unsigned ordinal){
    if(!active()||ordinal!=1||!route.disable_before(c,pc,w,si_completion_ack_trace))reject(5);
}
template<class C>bool poll(C& c){if(!route.poll(c,si_completion_ack_trace))reject(6);return false;}
}
