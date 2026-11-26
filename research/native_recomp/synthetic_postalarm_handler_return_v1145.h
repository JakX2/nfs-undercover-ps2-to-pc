#pragma once
#include "wii_callback_return_v846.h"
#include "v1139_private_postalarm_handler.h"
namespace undercover::wii::v1145 {
inline constexpr auto restore=[]{
    std::array<uint32_t,16> out{};
    for(unsigned i=0;i<15;++i)out[i]=0x800b0000u|((17u+i)<<21)|((0xffc4u+4u*i)&0xffffu);
    out.back()=0x4e800020u;return out;
}();
inline constexpr HandlerReturnExpectation expected{v1139::A+64u,v1139::A+128u,0x8003a000u,
    restore,{0x80010084u,0x7c0803a6u,0x38210080u,0x4e800020u},0x48001001u};
}
