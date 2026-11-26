#pragma once
#include "wii_held_pending_epilogue_v1149.h"
#include "v1145_private_postalarm_handler_return.h"
namespace undercover::wii::v1151 {
inline constexpr uint32_t Dest=v1145::expected.caller,En=Dest+0x1000u,Re=En+0x100u,Di=En+0x200u,Rs=En+0x300u,Lo=En+0x400u,T=En+0x500u,D=SiDispatchWitness::Dispatcher;
inline constexpr uint32_t Nop=0x60000000u,Rfi=0x4c000064u,Blr=0x4e800020u,Context=v958::context;
inline constexpr uint32_t branch(uint32_t a,uint32_t b){return 0x48000000u|((b-a)&0x03fffffcu);}
inline constexpr std::array<uint32_t,2> vec{Nop,Rfi},tramp{Nop,branch(T+4,D)};
inline constexpr std::array<uint8_t,8> image{0x60,0,0,0,0x4c,0,0,0x64};
inline constexpr LiveEpilogueExpectation epilogue{Dest,En,Re,Di,Rs,Lo,Lo+4,Context,4,8,21,255};
inline constexpr SecondVectorExpectation vector{T,D,Context,Nop,vec,tramp};
}
