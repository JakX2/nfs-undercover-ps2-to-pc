#pragma once
#include "wii_full_hardware_witness.h"
#include "v419_private_start_expectations.h"
#include "v425_private_hardware_expectations.h"
#include <cstdlib>
#include <iostream>

// V419 runtime hook ABI, with an independent opt-in hardware continuation.
namespace undercover::wii::v419 {
inline bool enabled() noexcept{
    static const bool active=[](){const char* e=std::getenv("UNDERCOVER_V419_START");return e&&e[0]=='1'&&e[1]=='\0';}();
    return active;
}
template<class Cpu> void observe(uint32_t addr,Cpu& cpu){
    static FullStartWitness start(expected);
    static FullHardwareWitness hardware(v425::expected_hardware);
    FullStartResult result;
    unsigned n;
    if(start.stage()<3u){
        result=start.observe(addr,cpu);n=start.stage();
        if(result==FullStartResult::Complete){
            if(!hardware.begin(cpu))result=FullStartResult::Invalid;
            else result=FullStartResult::Accepted;
        }
    }else{
        result=hardware.observe(addr,cpu);n=3u+hardware.stage();
    }
    if(result==FullStartResult::Invalid){
        std::cout<<"V425_HARDWARE_INVALID stage="<<n<<std::endl;std::_Exit(82);
    }
    std::cout<<"V425_HARDWARE_STAGE n="<<n<<" valid=1"<<std::endl;
    if(result==FullStartResult::Complete){
        std::cout<<"V425_HARDWARE_RESULT entry=1 registers=1 ps=1 fpr=1 cache_entry=1 fallback=0 boot_verified=0"<<std::endl;
        std::_Exit(0);
    }
}
[[noreturn]] inline void reject_interpreter(){
    std::cout<<"V425_HARDWARE_FALLBACK hit=1"<<std::endl;std::_Exit(83);
}
}
