#pragma once
#include "v813_private_callback_time.h"
#include "wii_postack_transfer_device_v771.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v813 {
inline thread_local CallbackTimeWitness route(expected);
inline bool active(){return route.stage()>=1&&route.stage()<=4;}
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V813_CALLBACK_TIME");
    return v&&v[0]=='1'&&v[1]=='\0';
}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V813_CALLBACK_TIME_INVALID kind="<<kind<<" stage="<<route.stage()
        <<" witness="<<route.failure()<<" device="<<si_transfer_device.failure()
        <<" visits="<<route.visits()<<" cursor="<<route.cursor()<<std::endl;std::_Exit(126);
}
template<class C>void start(C& c,uint32_t pc,uint32_t w,bool prefix_verified){
    // V807 has already observed the device and exact native tick at
    // this same resume label. Do not advance the device a second time.
    if(!route.start(c,pc,w,si_transfer_device.held_now(),prefix_verified)||
       !route.before(c,pc,w,si_transfer_device.held_now()))reject(1);
    std::cout<<"V813_CALLBACK_TIME_ENTRY prefix=1 follow=3"<<std::endl;
}
template<class C>bool poll(C& c){
    if(!route.poll(c,si_transfer_device.held_now()))reject(2);
    return false;
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    if(!route.entry(c,pc,si_transfer_device.held_now()))reject(3);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!si_transfer_device.after_return_at(c.inst_count)||
       !route.before(c,pc,w,si_transfer_device.held_now()))reject(4);
    if(route.stage()==5){
        std::cout<<std::dec<<"V813_CALLBACK_TIME_RESULT original_return=1 abi=1 leaves="<<route.cursor()
            <<" system_visits="<<route.time_visits()<<" leaf_visits="<<route.leaf_visits()
            <<" polls="<<route.polls()<<" reads="<<route.reads()<<" offset=1 follow="<<si_transfer_device.follow_stage()
            <<" continuation_executed=0 callback_return=0 boot_verified=0"<<std::endl;std::_Exit(0);
    }
}
}
