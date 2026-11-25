#pragma once
#include "v847_private_wireless_wrapper.h"
#include "wii_postack_transfer_device_v771.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v847 {
inline thread_local WirelessWrapperWitness route(expected);
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V847_WIRELESS");
    return v&&v[0]=='1'&&v[1]=='\0';
}
inline bool active(){return route.stage()==1u;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V847_WIRELESS_INVALID kind="<<kind<<" stage="<<route.stage()
        <<" witness="<<route.failure()<<" device="<<si_transfer_device.failure()
        <<" visits="<<route.visits()<<" writes="<<route.writes()<<std::endl;std::_Exit(126);
}
template<class C>void start(C& c,uint32_t pc,uint32_t w,bool frontier,unsigned ordinal){
    // V831 has already advanced the device for this precise call-site tick.
    if(!route.start(c,pc,w,frontier,si_transfer_device.held_now())||route.ordinal()!=ordinal)reject(1);
    std::cout<<"V847_WIRELESS_ENTRY frontier=1 ordinal="<<ordinal<<" changed="<<route.changed()<<std::endl;
}
inline void finish(){
    if(route.stage()==2u||route.stage()==3u){
        std::cout<<std::dec<<"V847_WIRELESS_RESULT ordinal="<<route.ordinal()
            <<" changed="<<route.changed()<<" visits="<<route.visits()<<" writes="<<route.writes()
            <<" returned="<<(route.stage()==2u)<<" lock_entry="<<(route.stage()==3u)
            <<" exi_executed=0 callback_return=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    if(!route.entry(c,pc,si_transfer_device.held_now()))reject(2);
    finish();return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!si_transfer_device.after_return_at(c.inst_count)||!route.before(c,pc,w,si_transfer_device.held_now()))reject(4);
    finish();
}
}
