#pragma once
#include "v786_private_alarm.h"
#include "wii_postack_transfer_device_v771.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v786 {
inline thread_local AlarmCancelReturnWitness route(expected);
inline bool active(){return route.stage()>=1&&route.stage()<=3;}
inline bool eligible(uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    const char* v=std::getenv("UNDERCOVER_V786_ALARM_RETURN");
    return v&&v[0]=='1'&&v[1]=='\0'&&!route.stage()&&ordinal==5&&kind==1&&pc==expected.site&&w==expected.branch;
}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V786_ALARM_INVALID kind="<<kind<<" route="<<route.failure()<<" queue="<<route.queue_failure()
        <<" mismatch="<<route.queue_mismatch()<<" device="<<si_transfer_device.failure()<<" stage="<<route.stage()
        <<" visits="<<route.visits()<<std::endl;std::_Exit(126);
}
template<class C>void start(C& c,uint32_t pc,uint32_t w){
    if(!route.start(c,pc,w,si_transfer_device.held_now()))reject(1);
    std::cout<<std::dec<<"V786_ALARM_ENTRY lane="<<route.lane()<<" timer="<<route.timer_required()<<std::endl;
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    if(!route.entry(c,pc,si_transfer_device.held_now()))reject(2);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!si_transfer_device.after_return_at(c.inst_count)||!route.native_before(c,pc,w,si_transfer_device.held_now()))reject(3);
}
template<class C>bool poll(C& c){
    if(!route.poll(c,si_transfer_device.held_now()))reject(4);
    return false;
}
template<class C>void returned(C& c,uint32_t pc,uint32_t w){
    // The handler boundary has already advanced the device witness once.
    if(!route.returned(c,pc,w,si_transfer_device.held_now()))reject(5);
    std::cout<<std::dec<<"V786_ALARM_RESULT original_return=1 queue=1 abi=1 lane="<<route.lane()
        <<" timer="<<route.timer_required()<<" deferred="<<route.deferred_clear()<<" calls="<<route.calls()
        <<" visits="<<route.total()<<" polls="<<route.polls()<<" follow="<<si_transfer_device.follow_stage()
        <<" handler_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);
}
}
