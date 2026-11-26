#pragma once
#include "wii_wireless_wrapper_v844.h"
#include "v831_private_callback_frontier.h"
namespace undercover::wii::v847 {
inline constexpr uint32_t A=v831::A,B=v831::B,U=0x8000f000u,D=0x8000f400u,R=0x8000f500u,L=0x8000f600u,SRAM=0x80030000u;
inline constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,P=v831::P;
inline constexpr auto setter=[] {std::array<uint32_t,39> x{};x.fill(Nop);x[0]=v831::branch(A,U);x[2]=Blr;return x;}();
inline constexpr auto getter=[] {std::array<uint32_t,30> x{};x.fill(Nop);x[0]=Blr;return x;}();
inline constexpr auto unlock=[] {std::array<uint32_t,184> x{};x.fill(Nop);x[0]=v831::branch(U,D);x[1]=0x90850048u;x[2]=v831::branch(U+8u,R);x[4]=Blr;return x;}();
inline constexpr auto disable=[] {std::array<uint32_t,5> x{};x.fill(Nop);x[0]=Blr;return x;}();
inline constexpr auto restore=[] {std::array<uint32_t,9> x{};x.fill(Nop);x[0]=Blr;return x;}();
inline constexpr WirelessExpectation expected{{{{A,setter},{B,getter},{U,unlock},{D,disable},{R,restore}}},
    {{{P+12u,v831::words[3].word,v831::words[4].word,3},{P+16u,v831::words[4].word,Nop,5}}},L,Nop,SRAM};
}
