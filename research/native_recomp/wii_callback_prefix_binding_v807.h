#pragma once
#include "v807_private_callback_prefix.h"
#include "v786_private_alarm.h"
#include "wii_callback_identity_v796.h"
#include "wii_callback_dispatch_device_v808.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v807 {
inline thread_local CallbackPrefixWitness<prefix.size(),save_words.size()> route(callback_root,save_root,prefix,save_words);
inline bool active(){return route.stage()>=1&&route.stage()<=5;}
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V807_CALLBACK_PREFIX");
    return v&&v[0]=='1'&&v[1]=='\0';
}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V807_CALLBACK_INVALID kind="<<kind<<" stage="<<route.stage()
        <<" witness="<<route.failure()<<" device="<<si_transfer_device.failure()
        <<" visits="<<route.visits()<<std::endl;std::_Exit(126);
}
template<class C>bool eligible(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    return enabled()&&!route.stage()&&si_transfer_device.follow_stage()==3&&si_transfer_device.held_now()&&
        c.ctr==callback_root&&classify_callback_identity(c,pc,w,ordinal,kind,
        v786::callback_candidate,v786::callback_words,v786::callback_sites)==2u;
}
template<class C>void start(C& c,uint32_t pc,uint32_t w,unsigned ordinal){
    if(!route.start_dispatch(c,pc,w,true,si_transfer_device.held_now()))reject(1);
    std::cout<<std::dec<<"V807_CALLBACK_ENTRY ordinal="<<ordinal<<" identity=1 follow=3"<<std::endl;
}
template<class C>bool poll(C& c){
    if(!route.dispatch_poll(c,si_transfer_device.held_now()))reject(2);
    return false;
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    // This is the existing outer dispatcher tick, not a new guest
    // instruction. The follow-on request must already be completed;
    // observing it cannot advance the SI scheduler or complete a token.
    if(route.stage()==1&&!observe_completed_callback_dispatch(si_transfer_device,c.inst_count))reject(3);
    if(!route.entry(c,pc,si_transfer_device.held_now()))reject(3);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!si_transfer_device.after_return_at(c.inst_count)||
       !route.before(c,pc,w,si_transfer_device.held_now()))reject(4);
    if(route.stage()==6){
        std::cout<<std::dec<<"V807_CALLBACK_RESULT original_prologue=1 save_return=1 stack_writes="<<route.writes()
            <<" visits="<<route.visits()<<" follow="<<si_transfer_device.follow_stage()
            <<" continuation_executed=0 callback_return=0 boot_verified=0"<<std::endl;std::_Exit(0);
    }
}
}
