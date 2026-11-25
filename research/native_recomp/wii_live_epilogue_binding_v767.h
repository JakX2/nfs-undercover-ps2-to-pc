#pragma once
#include "v767_private_epilogue_expectations.h"
#include "runtime/hw/hw.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v767 {
inline thread_local LiveEpilogueWitness route(expected);
inline thread_local ExternalReturnWitness* captured=nullptr;
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V767_EPILOGUE");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return route.stage()!=0;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V767_EPILOGUE_INVALID kind="<<kind<<" reason="<<route.failure()<<" stage="<<route.stage()<<" visits="<<route.visits()<<std::endl;std::_Exit(126);
}
inline uint32_t cause(){return nwii::runtime::hw::pi_intsr.load();}
inline uint32_t mask(){return nwii::runtime::hw::pi_intmr.load();}
inline void attach(ExternalReturnWitness& w){
    if(!enabled())return;
    if(captured||w.stage()!=1)reject(1);
    captured=&w;
}
template<class C>bool begin(C& c,uint32_t pc,uint32_t w){
    if(!enabled())return false;
    if(!captured||pc!=expected.dispatcher||!route.begin(c,*captured,cause(),mask()))reject(2);
    std::cout<<"V767_EPILOGUE_STAGE n=1"<<std::endl;
    if(!route.before(c,pc,w,cause(),mask()))reject(3);
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(!route.before(c,pc,w,cause(),mask()))reject(3);
    if(route.stage()==2)std::cout<<"V767_EPILOGUE_STAGE n=2"<<std::endl;
}
template<class C>void observe(uint32_t pc,C& c){
    if(route.stage()==4){
        if(pc!=resume_pc||c.pc!=pc)reject(4);
        return; // exact native label after the tick performs the final check
    }
    if(!route.entry(c,pc,cause(),mask()))reject(4);
}
template<class C>bool poll(C& c){
    const auto prior=route.stage();
    if(!route.poll(c,cause(),mask()))reject(5);
    if(route.stage()!=prior)std::cout<<"V767_EPILOGUE_STAGE n="<<route.stage()<<std::endl;
    return false;
}
template<class C>void resume(C& c,uint32_t pc,uint32_t w){
    if(!active())return;
    if(pc!=resume_pc||w!=resume_word||!route.resume(c,pc,w,cause(),mask()))reject(6);
    std::cout<<"V767_EPILOGUE_STAGE n=5"<<std::endl;
    std::cout<<std::dec<<"V767_EPILOGUE_RESULT live_context=1 scheduler=1 native_rfi=1 original_resume=1 visits="<<route.visits()<<" resumed_instruction_executed=0 boot_verified=0"<<std::endl;
    std::_Exit(0);
}
}
