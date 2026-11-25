#pragma once
#include "v922_private_irq_return.h"
#include "wii_saved_context_join_v921.h"
#include "wii_callback_return_binding_v850.h"
#include "runtime/hw/hw.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v922 {
inline thread_local LiveEpilogueWitness route(expected);
inline thread_local bool dispatch_seen=false;
inline bool active(){return route.stage()!=0u;}
inline uint32_t cause(){return nwii::runtime::hw::pi_intsr.load();}
inline uint32_t mask(){return nwii::runtime::hw::pi_intmr.load();}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V922_IRQ_RETURN_INVALID kind="<<kind<<" reason="<<route.failure()
             <<" stage="<<route.stage()<<" visits="<<route.visits()<<std::endl;std::_Exit(126);
}
inline void event(){std::cout<<"V922_IRQ_RETURN_STAGE n="<<route.stage()<<std::endl;}
template<class C>bool advance(C& c,bool outer=false){
    if(outer){
        if(!observe_completed_callback_dispatch(si_transfer_device,c.inst_count)||
           (v861::active()&&!v861::device.observe_dispatch(c.inst_count)))return false;
    }else if(!si_transfer_device.after_return_at(c.inst_count)||
             (v861::active()&&!v861::device.observe(c.inst_count)))return false;
    return v850::held(c);
}
template<class C>void begin(C& c,uint32_t pc,uint32_t w){
    auto* captured=v921::join.captured();
    if(active()||!captured||v921::join.context()!=expected.context||pc!=expected.dispatcher||
       !v850::held(c)||!route.begin(c,*captured,cause(),mask()))reject(1);
    event();
    // V920 already advanced the real device and label tick.
    if(!route.before(c,pc,w,cause(),mask()))reject(2);
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!advance(c)||!route.before(c,pc,w,cause(),mask()))reject(2);
    if(route.stage()==2u)event();
}
template<class C>bool poll(C& c){
    const unsigned prior=route.stage();
    if(!v850::held(c)||!route.poll(c,cause(),mask()))reject(3);
    if(route.stage()!=prior)event();
    return false;
}
template<class C>void observe(uint32_t pc,C& c){
    if(route.stage()==4u){
        // V616 native resume trace is BEFORE the original label tick but
        // AFTER the actual outer dispatcher tick.
        if(dispatch_seen||pc!=resume_pc||c.pc!=pc||!advance(c,true))reject(4);
        dispatch_seen=true;return;
    }
    if(!v850::held(c)||!route.entry(c,pc,cause(),mask()))reject(4);
}
template<class C>void resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!dispatch_seen||pc!=resume_pc||w!=resume_word||!advance(c)||
       !route.resume(c,pc,w,cause(),mask())||route.stage()!=5u)reject(5);
    event();
    std::cout<<std::dec<<"V922_IRQ_RETURN_RESULT original_context=1 scheduler=1 native_rfi=1 original_resume=1 visits="
             <<route.visits()<<" device_held=1 resumed_instruction_executed=0 boot_verified=0"<<std::endl;std::_Exit(0);
}
}
