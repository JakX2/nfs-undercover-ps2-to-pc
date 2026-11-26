#pragma once
#include "wii_callback_suffix_v841.h"
#include "v831_private_callback_frontier.h"
namespace undercover::wii::v1123 {
inline constexpr uint32_t R=v831::Root+44u,Restore=0x8000f800u;
inline constexpr std::array<CallbackSuffixWord,5> rows{{{R,0x60000000u},{R+4u,0x90810008u},
    {R+8u,0x4182fffcu},{R+12u,v831::branch(R+12u,Restore)},{R+16u,0x4e800421u}}};
inline constexpr CallbackSuffixExpectation expected{v831::Root,v831::Root+688u,R,rows,
    {{{R+16u,0u,4u},{R+12u,Restore,13u}}}};
}
