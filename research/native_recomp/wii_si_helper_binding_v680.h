#pragma once
#include "wii_si_first_helper_v680.h"
#include "v680_private_si_helper_expectations.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v680 {
inline thread_local SiFirstHelper helper(expected);
[[noreturn]]inline void reject(){
    std::cout<<"V680_SI_HELPER_INVALID reason="<<helper.failure()<<" stage="<<helper.stage()<<std::endl;
    std::_Exit(126);
}
template<class C>bool start(C& c,uint32_t pc,uint32_t word,unsigned ordinal,unsigned kind){
    if(ordinal!=1||kind!=1||helper.stage())return false;
    if(!helper.start(c,pc,word))reject();
    std::cout<<"V680_SI_HELPER_STAGE n=1"<<std::endl;
    return true;
}
template<class C>bool observe(uint32_t a,C& c){
    if(helper.stage()!=1)return false;
    if(!helper.entry(a,c))reject();
    std::cout<<"V680_SI_HELPER_STAGE n=2"<<std::endl;
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t word){
    if(si_completion_ack_trace.phase()==SiCompletionAckTrace::Phase::Idle)return;
    if(!helper.instruction(c,pc,word,si_completion_ack_trace))reject();
}
template<class C>void handler_boundary(C& c,uint32_t pc){
    if(helper.stage()>=1&&helper.stage()<=3){
        if(!helper.returned(c,pc))reject();
        std::cout<<"V680_SI_HELPER_STAGE n=3"<<std::endl;
    }
}
}
