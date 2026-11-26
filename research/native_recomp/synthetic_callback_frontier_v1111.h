#pragma once
#include "wii_callback_frontier_v829.h"
namespace undercover::wii::v831 {
inline constexpr uint32_t Root=0x8000d000u,P=Root+28u,A=0x8000e100u,B=0x8000e200u;
constexpr uint32_t branch(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
inline constexpr std::array<CallbackFrontierWord,5> words{{{P,0x60000000u},{P+4u,0x38600002u},
    {P+8u,0x90810008u},{P+12u,branch(P+12u,A)},{P+40u,branch(P+40u,B)}}};
inline constexpr CallbackFrontierExpectation expected{Root,Root+688u,P,words,{{{P+12u,A,3},{P+40u,B,5}}}};
}
