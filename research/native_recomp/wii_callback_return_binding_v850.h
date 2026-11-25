#pragma once
#include "v850_private_callback_return.h"
#include "wii_postack_transfer_device_v771.h"
#include "wii_callback_dispatch_device_v808.h"
#include <cstdlib>
#include <iostream>
#include <optional>
namespace undercover::wii::v850 {
inline thread_local CallbackSuffixWitness suffix(suffix_expected);
inline thread_local std::optional<CallbackReturnWitness> returned;
inline thread_local const Caller* caller=nullptr;
inline thread_local const void* captured_cpu=nullptr;
inline thread_local std::array<uint32_t,32> original_gp{};
inline thread_local uint32_t original_cr=0;
inline bool enabled(){
    const char* v=std::getenv("UNDERCOVER_V850_CALLBACK_RETURN");
    return v&&v[0]=='1'&&v[1]=='\0';
}
inline bool active(){return suffix.stage()==1u||(returned&&returned->stage()>=1u&&returned->stage()<=4u);}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V850_CALLBACK_RETURN_INVALID kind="<<kind<<" suffix_stage="<<suffix.stage()
        <<" suffix_reason="<<suffix.failure()<<" return_stage="<<(returned?returned->stage():0u)
        <<" return_reason="<<(returned?returned->failure():0u)
        <<" device="<<si_transfer_device.failure()<<std::endl;std::_Exit(126);
}
template<class C>uint32_t pack(C& c){
    uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
}
template<class C>void capture(C& c,uint32_t pc,uint32_t w,unsigned ordinal){
    if(!enabled())return;
    if(captured_cpu||caller||returned||suffix.stage()||!si_transfer_device.held_now())reject(1);
    for(const auto& x:callers)if(x.site==pc&&x.word==w&&x.ordinal==ordinal)caller=&x;
    if(!caller)reject(1);
    captured_cpu=&c;original_gp=c.gpr;original_cr=pack(c);
}
template<class C>void suffix_before(C& c,uint32_t pc,uint32_t w){
    if(!suffix.before(c,pc,w,si_transfer_device.held_now()))reject(2);
    if(suffix.stage()!=2u)return;
    std::cout<<std::dec<<"V850_CALLBACK_SUFFIX_RESULT ordinal="<<suffix.ordinal()
        <<" target_class="<<suffix.target_class()<<" visits="<<suffix.visits()
        <<" writes="<<suffix.writes()<<" polls="<<suffix.polls()
        <<" setter_return=1 callback_return=0 boot_verified=0"<<std::endl;
    // No unknown indirect callback is admitted, even if its CTR is mapped.
    if(suffix.ordinal()!=13u)std::_Exit(0);
    if(!caller||returned)reject(3);
    returned.emplace(caller->returned);
    if(!returned->start_dispatch(c,pc,w,original_gp,original_cr,si_transfer_device.held_now()))reject(3);
}
template<class C>void start(C& c,uint32_t pc,uint32_t w,bool setter_verified){
    if(captured_cpu!=&c||!caller||!suffix.start(c,pc,w,setter_verified,si_transfer_device.held_now()))reject(1);
    std::cout<<"V850_CALLBACK_SUFFIX_ENTRY setter_return=1 handler_ordinal="<<caller->ordinal<<std::endl;
    // V847 observed this exact resume tick.
    suffix_before(c,pc,w);
}
template<class C>bool poll(C& c){
    if(suffix.stage()==1u){
        if(!suffix.poll(c,si_transfer_device.held_now()))reject(4);
    }else if(!returned||!returned->dispatch_poll(c,si_transfer_device.held_now()))reject(4);
    return false;
}
template<class C>bool observe(uint32_t pc,C& c){
    if(!active())return false;
    if(!returned||!returned->entry(c,pc,si_transfer_device.held_now()))reject(5);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!si_transfer_device.after_return_at(c.inst_count))reject(6);
    if(suffix.stage()==1u)suffix_before(c,pc,w);
    else if(!returned||!returned->before(c,pc,w,si_transfer_device.held_now())||returned->stage()==5u)reject(6);
}
template<class C>void dispatch_resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    // The outer dispatcher has incremented the real counter already.
    if(!returned||!caller||!observe_completed_callback_dispatch(si_transfer_device,c.inst_count)||
       !returned->dispatch_resume(c,pc,w,si_transfer_device.held_now()))reject(7);
}
template<class C>void handler_resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    // The resumed handler label contributes exactly one additional native tick.
    if(!returned||!caller||!si_transfer_device.after_return_at(c.inst_count)||
       !returned->before(c,pc,w,si_transfer_device.held_now())||returned->stage()!=5u)reject(7);
    std::cout<<std::dec<<"V850_CALLBACK_RETURN_RESULT handler_ordinal="<<caller->ordinal
        <<" restore=1 callback_return=1 abi=1 outer_dispatch=1 visits="<<returned->visits()
        <<" handler_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);
}
}
