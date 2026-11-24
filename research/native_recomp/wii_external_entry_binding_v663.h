#pragma once
#include "v663_private_external_expectations.h"
#include "runtime/hw/hw.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v663 {
inline thread_local ColdExternalEntry route(expected);
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V663_EXTERNAL");return v&&v[0]=='1'&&v[1]=='\0';}
[[noreturn]] inline void reject(unsigned n){
    std::cout<<"V663_EXTERNAL_INVALID reason="<<n<<" stage="<<route.stage()<<std::endl;
    std::_Exit(124);
}
inline void event(){std::cout<<"V663_EXTERNAL_STAGE n="<<route.stage()<<std::endl;}
template<class C> void begin(C& c,uint32_t cause,uint32_t mask){
    if(!route.begin(c,cause,mask)){
        std::cout<<"V663_EXTERNAL_PENDING active="<<(cause&mask)<<std::endl;
        reject(route.failure());
    }
    event();
}
template<class C> bool poll(C& c){
    using namespace nwii::runtime::hw;
    bool entered=route.poll(c,pi_intsr.load(),pi_intmr.load());
    if(route.failure())reject(route.failure());
    if(entered)event();
    return entered;
}
template<class C> void observe(uint32_t a,C& c){
    using namespace nwii::runtime::hw;
    if(!route.observe(a,c,pi_intsr.load(),pi_intmr.load())){
        if(route.failure()==6u)std::cout<<"V670_VECTOR_REFUSAL mask="<<route.vector_refusal()<<std::endl;
        reject(route.failure());
    }
    event();
    if(route.stage()==6){
        std::cout<<"V663_EXTERNAL_RESULT vector=1 saved_context=1 dispatcher=1 si_pending=1 ack=0 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
}
