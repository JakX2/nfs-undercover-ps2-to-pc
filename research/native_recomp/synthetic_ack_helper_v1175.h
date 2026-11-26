#pragma once
#include "v1167_private_third_ack.h"
namespace undercover::wii::v1175 {
using v1167::Handler;using v1167::Save;using v1167::Helper;
inline constexpr uint32_t Nested=0x8003c200u,Disable=Nested+0x100u,Time=Nested+0x200u,Restore=Nested+0x300u;
inline constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,Mtmsr=0x7c600124u;
inline constexpr uint32_t link(uint32_t a,uint32_t b){return v1151::branch(a,b)|1u;}
inline constexpr std::array<AckCallSpan,7> spans{{{Handler,Handler+16u},{Save,Save+4u},{Helper,Helper+32u},
 {Nested,Nested+20u},{Disable,Disable+8u},{Time,Time+8u},{Restore,Restore+8u}}};
inline constexpr std::array<AckCallEdge,6> edges{{{Handler,Save},{Handler+4u,Helper},{Helper+20u,Nested},
 {Nested,Disable},{Nested+4u,Time},{Nested+8u,Restore}}};
inline constexpr std::array<AckMsrSite,2> msr{{{Disable,Mtmsr},{Restore,Mtmsr}}};
inline constexpr std::array<ThirdAckNativeLabel,16> labels{{
 {Helper+20u,link(Helper+20u,Nested),Helper,false},{Nested,link(Nested,Disable),Nested,false},
 {Disable,Mtmsr,Disable,false},{Disable+4u,Blr,Disable,false},{Nested+4u,link(Nested+4u,Time),Nested,false},
 {Time,Nop,Time,false},{Time+4u,Blr,Time,false},{Nested+8u,link(Nested+8u,Restore),Nested,false},
 {Restore,Mtmsr,Restore,false},{Restore+4u,Blr,Restore,false},{Nested+12u,Nop,Nested,false},
 {Nested+16u,Blr,Nested,false},{Helper+24u,Nop,Helper,false},{Helper+28u,Blr,Helper,false},{Handler+8u,Nop,Handler,false},{Handler+12u,0x4e800421u,Handler,true}}};
inline constexpr HeldAckHelperExpectation expected{Handler+8u,Nop,15,6,6,2};
inline constexpr bool callback_guard=true;
inline constexpr auto callback_words=v958::third_postalarm_prefix;
inline constexpr std::array<uint32_t,2> callback_sites{Handler+12u,Handler+16u};
inline constexpr HeldAckCallbackExpectation callback_expected{callback_sites[0],0x4e800421u,1u,6u};
#ifdef UNDERCOVER_V1205_PRIVATE_ACK_RETURN
inline constexpr unsigned return_loads=2;
inline constexpr NativeReturnExpectation<return_loads> return_expected{v1123::R+12u,v1123::Restore,Handler+16u,
    {0x83cbfff8u,0x83ebfffcu,Blr},{0x80010044u,0x7c0803a6u,0x38210040u,Blr},Nop};
#endif
}
