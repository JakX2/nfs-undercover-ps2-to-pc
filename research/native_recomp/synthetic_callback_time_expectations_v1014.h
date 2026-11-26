#pragma once
#include "wii_callback_time_v810.h"
namespace undercover::wii::v813 {
inline constexpr uint32_t C=0x8000d000u,T=0x8000f000u,D=T+0x100u,U=T+0x200u,R=T+0x300u,Offset=T+0x500u;
inline constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t branch(uint32_t from,uint32_t to){return 0x48000001u|((to-from)&0x03fffffcu);}
constexpr uint32_t mftb(unsigned reg,unsigned spr){return (31u<<26)|(reg<<21)|((spr&31u)<<16)|((spr>>5)<<11)|(371u<<1);}
inline constexpr std::array<uint32_t,3> continuation{Nop,branch(C+24,T),Nop};
inline constexpr auto system_words=[]{
    std::array<uint32_t,25> w{};w.fill(Nop);
    w[1]=branch(T+4,D);w[4]=branch(T+16,U);w[7]=branch(T+28,R);w[24]=Blr;return w;
}();
inline constexpr std::array<uint32_t,6> disable{Nop,0x7cc00124u,Nop,Nop,Nop,Blr};
inline constexpr std::array<uint32_t,6> timebase{mftb(3,269),mftb(4,268),mftb(5,269),0x4082fff4u,Nop,Blr};
inline constexpr std::array<uint32_t,6> restore=disable;
inline constexpr CallbackTimeExpectation expected{C,C+688,C+20,C+24,T,continuation,system_words,
    {{{T+4,D,D+24,system_words[1],1},{T+16,U,U+24,system_words[4],2},{T+28,R,R+24,system_words[7],3}}},Offset};
}
