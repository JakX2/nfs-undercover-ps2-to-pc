#pragma once
#include "wii_boot_sc_route_v570.h"
#include "v574_private_sc_expectations.h"
#include "runtime/cpu_context.h"
#include <cstdlib>
#include <iostream>

// The generated native vector remains outside the generic dispatcher.
extern "C" void func_80000C00(nwii::runtime::CPUContext&);
namespace undercover::wii::v574 {
inline BootScRoute route(expected_vector);
inline bool enabled() noexcept {
    static const bool on=[](){const char* v=std::getenv("UNDERCOVER_V574_SC");
        return v&&v[0]=='1'&&v[1]=='\0';}();
    return on;
}
[[noreturn]] inline void reject(){
    std::cout<<"V574_DSP_SC_INVALID rejected=1"<<std::endl;std::_Exit(113);
}
inline void arm(uint32_t addr,nwii::runtime::CPUContext& c){
    if(!enabled())reject();
    try{route.arm(addr,c);}
    catch(const std::exception&){reject();}
    std::cout<<"V574_DSP_SC_STAGE n=1"<<std::endl;
}
inline bool vector_trace(uint32_t addr,nwii::runtime::CPUContext& c){
    if(addr!=BootScRoute::Vector&&route.phase()!=BootScRoute::Phase::Executing)return false;
    if(!enabled())reject();
    try{if(!route.vector_trace(addr,c))reject();}
    catch(const std::exception&){reject();}
    std::cout<<"V574_DSP_SC_STAGE n=2"<<std::endl;
    return true;
}
inline bool try_sc(nwii::runtime::CPUContext& c){
    if(!enabled())return false;
    try{
        const bool consumed=route.dispatch(c,[](auto& cpu){::func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i){
                    const uint32_t expected=i==9?hid:i==10?(hid|8u):gp[i];
                    if(cpu.gpr[i]!=expected)return false;
                }
                return true;
            });
        if(consumed)std::cout<<"V574_DSP_SC_STAGE n=3"<<std::endl;
        return consumed;
    }catch(const std::exception&){reject();}
}
}
