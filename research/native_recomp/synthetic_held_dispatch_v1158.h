#pragma once
#include "v1151_private_held_epilogue.h"
namespace undercover::wii::v1158 {
inline constexpr auto expected=[]{
    SiDispatchExpectations e{};
    e.dispatcher_word=v1151::Nop;e.handler_word=v1151::branch(SiDispatchWitness::Handler,0x8003c000u)|1u;
    e.indirect_pc=v1151::D+16u;e.indirect_word=0x4e800421u;
    for(unsigned i=0;i<4;++i){
        const uint32_t site=v1151::D+0x20u+4u*i,dst=v1151::D+0x1000u+0x100u*i;
        e.edges[i]={dst,site+4u,v1151::branch(site,dst)|1u,v1151::Nop};
    }
    return e;
}();
}
