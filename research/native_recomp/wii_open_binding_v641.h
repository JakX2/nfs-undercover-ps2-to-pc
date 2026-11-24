#pragma once
#include "wii_boot_sc_binding_v574.h"
#include "wii_open_sc_route_v637.h"
namespace undercover::wii::v641 {
inline OpenScRoute route(v574::expected_vector);
inline bool active=false;
[[noreturn]]inline void reject(){
    std::cout<<"V641_OPEN_SC_INVALID rejected=1"<<std::endl;std::_Exit(122);
}
inline bool vector_trace(uint32_t addr,nwii::runtime::CPUContext& c){
    if(!active||addr!=OpenScRoute::Vector)return false;
    try{if(!route.vector_trace(addr,c))reject();}
    catch(const std::exception&){reject();}
    std::cout<<"V641_OPEN_VECTOR entered=1"<<std::endl;return true;
}
inline bool try_sc(nwii::runtime::CPUContext& c){
    if(!active)return false;
    try{
        if(!route.dispatch(c,[](auto& cpu){::func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }))reject();
        std::cout<<"V641_OPEN_RFI returned=1"<<std::endl;return true;
    }catch(const std::exception&){reject();}
}
}
