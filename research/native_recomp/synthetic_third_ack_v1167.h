#pragma once
#include "v1158_private_held_dispatch.h"
namespace undercover::wii::v1167 {
inline constexpr uint32_t Handler=SiDispatchWitness::Handler,Save=0x8003c000u,Helper=0x8003c100u;
inline constexpr uint32_t CallSave=v1151::branch(Handler,Save)|1u,CallHelper=v1151::branch(Handler+4u,Helper)|1u;
inline constexpr std::array<AckCallSpan,3> spans{{{Handler,Handler+16u},{Save,Save+4u},{Helper,Helper+24u}}};
inline constexpr std::array<AckCallEdge,2> edges{{{Handler,Save},{Handler+4u,Helper}}};
inline constexpr std::array<AckMsrSite,0> msr{};
}
