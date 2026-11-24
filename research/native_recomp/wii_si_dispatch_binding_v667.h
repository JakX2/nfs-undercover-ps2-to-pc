#pragma once
#include "v667_private_si_dispatch_expectations.h"
#include "wii_si_binding_v512.h"
#include "runtime/hw/hw.h"
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v667 {
inline thread_local SiDispatchWitness route(expected);
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V667_SI_DISPATCH");return v&&v[0]=='1'&&v[1]=='\0';}
[[noreturn]] inline void reject(unsigned n){
    std::cout<<"V667_SI_DISPATCH_INVALID reason="<<n<<" stage="<<route.stage()<<std::endl;std::_Exit(125);
}
inline void event(){std::cout<<"V667_SI_DISPATCH_STAGE n="<<route.stage()<<std::endl;}
inline uint32_t read(uint32_t address){
    auto v=SiBinding::read32(address);if(!v)reject(6);return *v;
}
template<class C>void begin(C& c){
    using namespace nwii::runtime::hw;
    if(!route.begin(c,pi_intsr.load(),pi_intmr.load(),read(0xcd006434u),read(0xcd006438u)))reject(route.failure());
    event();
}
template<class C>bool poll(C& c){
    using namespace nwii::runtime::hw;
    if(!route.poll(c,pi_intsr.load(),pi_intmr.load()))reject(route.failure());
    return false; // EE is masked, and no callback is allowed in this bounded route.
}
template<class C>void observe(uint32_t a,C& c){
    using namespace nwii::runtime::hw;
    if(!route.observe(a,c,pi_intsr.load(),pi_intmr.load(),read(0xcd006434u),read(0xcd006438u)))reject(route.failure());
    event();
    if(route.stage()==6){
        std::cout<<"V667_SI_DISPATCH_RESULT pi_reads=1 timebase=1 scheduler_disable=1 handler=1 index=20 si_pending=1 ack=0 rfi_return=0 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
}
