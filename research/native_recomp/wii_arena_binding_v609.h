#pragma once
#include "wii_boot_sc_binding_v574.h"
#include "wii_arena_sc_pair_v598.h"
#include "wii_arena_reset_v606.h"
#include <memory>
namespace undercover::wii::v609 {
inline ArenaScPair pair(v574::expected_vector);
inline ArenaResetProfile reset;
inline std::unique_ptr<ArenaResetBinding> binding;
inline bool active=false;
[[noreturn]] inline void reject(){
    std::cout<<"V609_ARENA_SC_INVALID rejected=1"<<std::endl;std::_Exit(117);
}
inline bool enable(){
    const char* mode=std::getenv("UNDERCOVER_V609_ARENA");
    if(active||binding||!v574::enabled()||!mode||mode[0]!='1'||mode[1]!='\0')return false;
    try{binding=std::make_unique<ArenaResetBinding>(reset);}catch(const std::exception&){return false;}
    active=true;return true;
}
inline bool vector_trace(uint32_t addr,nwii::runtime::CPUContext& c){
    if(!active||addr!=BootScRoute::Vector)return false;
    try{if(!pair.vector_trace(addr,c))reject();}
    catch(const std::exception&){reject();}
    std::cout<<"V609_ARENA_VECTOR lane="<<pair.completed()+1u<<std::endl;
    return true;
}
inline bool try_sc(nwii::runtime::CPUContext& c){
    if(!active)return false;
    try{
        if(!pair.dispatch(c,[](auto& cpu){::func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }))reject();
        std::cout<<"V609_ARENA_SC lane="<<pair.completed()+1u<<std::endl;
        return true;
    }catch(const std::exception&){reject();}
}
}
