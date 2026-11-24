#pragma once
#include "wii_full_start_witness.h"
// Generated privately from the SHA-verified owner DOL, never committed.
#include "v419_private_start_expectations.h"
#include <cstdlib>
#include <iostream>

namespace undercover::wii::v419 {
inline bool enabled() noexcept{
    static const bool active=[](){const char* e=std::getenv("UNDERCOVER_V419_START");return e&&e[0]=='1'&&e[1]=='\0';}();
    return active;
}
template<class Cpu> void observe(uint32_t addr,Cpu& cpu){
    static FullStartWitness witness(expected);
    const auto result=witness.observe(addr,cpu);
    if(result==FullStartResult::Invalid){
        std::cout<<"V419_FULL_START_INVALID stage="<<witness.stage()<<std::endl;
        std::_Exit(82);
    }
    std::cout<<"V419_FULL_START_STAGE n="<<witness.stage()<<" valid=1"<<std::endl;
    if(result==FullStartResult::Complete){
        // Dedicated bounded process: stop before the real hardware body.
        // No guest register/PC or original DOL changes and no boot claim.
        std::cout<<"V419_FULL_START_RESULT entry=1 registers=1 hardware_entry=1 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
[[noreturn]] inline void reject_interpreter(){
    std::cout<<"V419_FULL_START_FALLBACK hit=1"<<std::endl;
    std::_Exit(83);
}
}
