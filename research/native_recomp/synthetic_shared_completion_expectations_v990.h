#pragma once
#define UNDERCOVER_V975_PRIVATE_TIME 1
#define UNDERCOVER_V989_PRIVATE_SHARED 1
#include "wii_bounded_ack_call_route_v956.h"
namespace undercover::wii::v958 {
inline constexpr uint32_t context=0x80009000u;
inline constexpr std::array<AckCallSpan,4> spans{{{0x80004000u,0x80004018u},{0x80004100u,0x80004104u},{0x80004200u,0x80004220u},{0x80004300u,0x80004314u}}};
inline constexpr std::array<AckCallEdge,3> edges{{{0x80004000u,0x80004100u},{0x80004004u,0x80004200u},{0x80004218u,0x80004300u}}};
inline constexpr uint32_t time_call=0x8000400cu;
inline constexpr std::array<AckCallSpan,7> time_spans{{spans[0],spans[1],spans[2],spans[3],
    {0x80004400u,0x80004408u},{0x80004500u,0x80004508u},{0x80004600u,0x80004608u}}};
inline constexpr std::array<AckCallEdge,7> time_edges{{edges[0],edges[1],edges[2],{time_call,0x80004300u},
    {0x80004300u,0x80004400u},{0x80004304u,0x80004500u},{0x80004308u,0x80004600u}}};
inline constexpr std::array<AckMsrSite,2> msr_sites{{{0x80004400u,0x7c600124u},{0x80004600u,0x7c600124u}}};
inline constexpr uint32_t completion_time_call=0x8000420cu;
inline constexpr std::array<AckCallEdge,8> shared_edges{{time_edges[0],time_edges[1],time_edges[2],time_edges[3],
    time_edges[4],time_edges[5],time_edges[6],{completion_time_call,0x80004300u}}};
}
