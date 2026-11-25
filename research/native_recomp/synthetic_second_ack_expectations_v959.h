#pragma once
#include "wii_bounded_ack_call_route_v956.h"
namespace undercover::wii::v958 {
inline constexpr uint32_t context=0x80009000u;
inline constexpr std::array<AckCallSpan,4> spans{{{0x80004000u,0x80004010u},{0x80004100u,0x80004104u},{0x80004200u,0x80004214u},{0x80004300u,0x80004304u}}};
inline constexpr std::array<AckCallEdge,3> edges{{{0x80004000u,0x80004100u},{0x80004004u,0x80004200u},{0x8000420cu,0x80004300u}}};
}
