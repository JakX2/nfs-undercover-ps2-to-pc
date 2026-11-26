#pragma once
#include "wii_callback_return_v846.h"
#include "v1123_private_postalarm_suffix.h"
namespace undercover::wii::v1132 {
inline constexpr std::array<uint32_t,7> restore{0x834bffe8u,0x836bffecu,0x838bfff0u,0x83abfff4u,0x83cbfff8u,0x83ebfffcu,0x4e800020u};
inline constexpr std::array<uint32_t,4> tail{0x80010044u,0x7c0803a6u,0x38210040u,0x4e800020u};
inline constexpr CallbackReturnExpectation expected{v1123::R+12u,v1123::Restore,0x80004030u,restore,tail,0x60000000u};
}
