#pragma once
#include "v831_private_callback_frontier.h"
#include "wii_postack_transfer_device_v771.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v831 {
inline thread_local CallbackFrontierWitness route(expected);
inline thread_local const void* captured_cpu=nullptr;
inline thread_local unsigned channel=4u;
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V831_CALLBACK_FRONTIER");
    return v&&v[0]=='1'&&v[1]=='\0';
}
inline bool active(){return route.stage()==1u;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V831_CALLBACK_FRONTIER_INVALID kind="<<kind<<" stage="<<route.stage()
        <<" witness="<<route.failure()<<" device="<<si_transfer_device.failure()
        <<" visits="<<route.visits()<<" writes="<<route.writes()<<std::endl;std::_Exit(126);
}
template<class C>void capture(C& c){
    if(!enabled())return;
    if(captured_cpu||route.stage()||c.gpr[3]>3u||!si_transfer_device.held_now()||
       si_transfer_device.follow_stage()!=3u)reject(1);
    captured_cpu=&c;channel=c.gpr[3];
}
inline void finish(){
    if(route.stage()==2u){
        std::cout<<std::dec<<"V831_CALLBACK_FRONTIER_RESULT ordinal="<<route.ordinal()
            <<" visits="<<route.visits()<<" writes="<<route.writes()<<" zero_id="<<route.zero_id()
            <<" follow="<<si_transfer_device.follow_stage()<<" store_bytes=1 wireless_executed=0 callback_return=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
template<class C>void start(C& c,uint32_t pc,uint32_t w,bool time_verified){
    // V813 already observed this exact native tick and device state.
    if(captured_cpu!=&c||!route.start(c,pc,w,channel,time_verified,si_transfer_device.held_now())||
       !route.before(c,pc,w,si_transfer_device.held_now()))reject(2);
    std::cout<<"V831_CALLBACK_FRONTIER_ENTRY original_time_return=1 follow=3"<<std::endl;
    finish();
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!si_transfer_device.after_return_at(c.inst_count)||
       !route.before(c,pc,w,si_transfer_device.held_now()))reject(4);
    finish();
}
}
