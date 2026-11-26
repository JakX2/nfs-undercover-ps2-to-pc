#pragma once
#include "wii_second_ack_live_v958.h"
#include "runtime/cpu_context.h"
extern "C" void func_80000C00(nwii::runtime::CPUContext&);
namespace undercover::wii::v1246 {
inline bool try_sc(nwii::runtime::CPUContext& c){
    return v958::ack_open_syscall(c,[](auto& cpu){::func_80000C00(cpu);},
        [](const auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        });
}
}
