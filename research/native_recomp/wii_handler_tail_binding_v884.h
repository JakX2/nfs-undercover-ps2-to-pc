#pragma once
#include "v884_private_handler_tail.h"
#include "wii_si_handler_return_binding_v726.h"
#include "wii_callback_return_binding_v850.h"
namespace undercover::wii::v884 {
inline thread_local HandlerNativeReturnWitness returned(expected);
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V884_HANDLER_TAIL");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return returned.stage()!=0u;}
[[noreturn]]inline void reject(unsigned reason){
    std::cout<<std::dec<<"V884_HANDLER_TAIL_INVALID reason="<<reason<<" witness="<<returned.failure()<<" stage="<<returned.stage()<<" handler="<<v726::witness.failure()<<std::endl;std::_Exit(126);
}
template<class C>void advance(C& c,bool dispatch=false){
    if(dispatch){
        if(!observe_completed_callback_dispatch(si_transfer_device,c.inst_count))reject(2);
        if(v861::active()&&!v861::device.observe_dispatch(c.inst_count))reject(2);
    }else{
        if(!si_transfer_device.after_return_at(c.inst_count))reject(2);
        if(v861::active()&&!v861::device.observe(c.inst_count))reject(2);
    }
    if(!v850::held(c))reject(2);
}
template<class C>bool start(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    if(!enabled()||ordinal!=12u||kind!=1u)return false;
    if(active()||pc!=expected.call||!v850::held(c)||si_transfer_device.follow_stage()!=3u||
       !v726::witness.before_authenticated(c,pc,w,true,12u)||
       !returned.start_dispatch(c,pc,w,v726::witness.entry_gprs(),v726::witness.entry_cr(),true))reject(1);
    std::cout<<"V884_HANDLER_TAIL_ENTRY ordinal=12 authenticated=1 follow_held=1"<<std::endl;
    return true;
}
template<class C>void observe(uint32_t pc,C& c){
    if(!active()||!v850::held(c)||!returned.entry(c,pc,true))reject(3);
}
template<class C>void before_alias(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    advance(c);
    if(returned.stage()!=2u||!returned.before(c,pc,w,true))reject(4);
}
template<class C>void handler_before(C& c,uint32_t pc,uint32_t w,unsigned ordinal,unsigned kind){
    advance(c);
    if(ordinal||kind||returned.stage()!=3u)reject(4);
    if(pc==expected.call+4u&&!v726::witness.restore_returned(c,pc,16u,true,12u))reject(4);
    if(!returned.before(c,pc,w,true)||!v726::witness.before(c,pc,w,true))reject(4);
    if((returned.stage()==4u)!=(v726::witness.stage()==3u))reject(4);
}
template<class C>bool poll(C& c){
    if(!v850::held(c)||!returned.dispatch_poll(c,true)||!v726::witness.poll(c,true))reject(5);
    return false;
}
template<class C>void dispatch_resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    advance(c,true);
    if(!returned.dispatch_resume(c,pc,w,true))reject(6);
}
template<class C>void resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    advance(c);
    if(!returned.before(c,pc,w,true)||returned.stage()!=5u||
       !v726::witness.resumed(c,pc,w,true)||v726::witness.stage()!=5u)reject(6);
    std::cout<<"V884_HANDLER_TAIL_RESULT original_return=1 restore_gprs=15 abi=1 outer_dispatch=1 follow_held=1 dispatcher_instruction_executed=0 rfi_return=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
}
