#pragma once
#include "v868_private_handler_suffix.h"
#include "wii_si_handler_return_binding_v726.h"
#include "wii_callback_return_binding_v850.h"
namespace undercover::wii::v868 {
inline thread_local HandlerSuffixGuard guard;
inline thread_local unsigned lane=0;
inline bool active(){return lane!=0u;}
[[noreturn]]inline void reject(unsigned reason){
    std::cout<<std::dec<<"V868_HANDLER_SUFFIX_INVALID reason="<<reason<<" guard="<<guard.failure()
        <<" handler="<<v726::witness.failure()<<" visits="<<guard.visits()<<" writes="<<guard.writes()<<std::endl;std::_Exit(126);
}
template<class C>bool before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    if(!v850::continue_handler()||!v850::returned||v850::returned->stage()!=5u)return false;
    if(!active()){
        if(!v850::caller||v850::captured_cpu!=&c||pc!=v850::caller->site+4u||!v850::held(c))reject(1);
        lane=v850::caller->ordinal;
        if(lane!=6u&&lane!=11u)reject(1);
        if(!v726::witness.callback_returned(c,pc,v850::captured_tick,true,v850::held(c),lane)||
           !guard.start(c,lane==6u?std::span<const HandlerSuffixLabel>(after6):std::span<const HandlerSuffixLabel>(after11),pc))reject(1);
        std::cout<<"V868_HANDLER_SUFFIX_ENTRY ordinal="<<lane<<" callback_return=1 same_tick=1"<<std::endl;
    }else{
        if(!si_transfer_device.after_return_at(c.inst_count))reject(2);
        if(v861::active()&&!v861::device.observe(c.inst_count))reject(2);
    }
    if(!v850::held(c)||!guard.before(c,pc,w,ordinal,kind))reject(3);
    if(kind){
        if(!((lane==6u&&kind==1u&&(ordinal==7u||ordinal==8u||ordinal==12u))||
             (lane==11u&&((kind==2u&&ordinal==11u)||(kind==1u&&ordinal==12u))))||
           !v726::witness.stop_before_call(c,pc,w,true,ordinal,kind))reject(4);
        std::cout<<std::dec<<"V868_HANDLER_SUFFIX_RESULT after="<<lane<<" next="<<ordinal<<" kind="<<kind
            <<" visits="<<guard.visits()<<" writes="<<guard.writes()<<" executed=0 handler_return=0 boot_verified=0"<<std::endl;std::_Exit(0);
    }
    if(!v726::witness.before(c,pc,w,true)||v726::witness.stage()!=2u)reject(4);
    return true;
}
template<class C>bool poll(C& c){
    if(!v850::held(c)||!v726::witness.poll(c,true))reject(5);
    return false;
}
}
