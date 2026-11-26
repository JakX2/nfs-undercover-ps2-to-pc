#pragma once
#define UNDERCOVER_V975_PRIVATE_TIME 1
#define UNDERCOVER_V989_PRIVATE_SHARED 1
#define UNDERCOVER_V981_PRIVATE_FRONTIER 1
#define UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER 1
#define UNDERCOVER_V1009_PRIVATE_CALLBACK 1
#include "wii_bounded_ack_call_route_v956.h"
namespace undercover::wii::v958 {
inline constexpr uint32_t context=0x80009000u;
inline constexpr std::array<AckCallSpan,4> spans{{{0x80004000u,0x80004020u},{0x80004100u,0x80004104u},{0x80004200u,0x80004220u},{0x80004300u,0x80004314u}}};
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
inline constexpr uint32_t transfer_call=0x80004014u,transfer_branch=0x480006edu,transfer_callback=0x8000d000u;
inline constexpr uint32_t transfer_data=0x8000c000u,transfer_slots=0x8000c100u;
inline constexpr uint32_t second_callback_save_root=0x8000e000u;
inline constexpr std::array<uint32_t,6> second_callback_prefix{0x9421ffc0u,0x7c0802a6u,0x90010044u,0x39610040u,0x48000ff1u,0x60000000u};
inline constexpr std::array<uint32_t,7> second_callback_save{0x934bffe8u,0x936bffecu,0x938bfff0u,0x93abfff4u,0x93cbfff8u,0x93ebfffcu,0x4e800020u};
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
inline constexpr std::array<uint32_t,8> success_callback_words{second_callback_prefix[0],second_callback_prefix[1],second_callback_prefix[2],second_callback_prefix[3],second_callback_prefix[4],second_callback_prefix[5],0x48001fe9u,0x60000000u};
#else
inline constexpr std::array<uint32_t,7> success_callback_words{second_callback_prefix[0],second_callback_prefix[1],second_callback_prefix[2],second_callback_prefix[3],second_callback_prefix[4],second_callback_prefix[5],0x4e800020u};
#endif
inline constexpr std::array<uint32_t,2> success_callback_sites{0x80004018u,0x8000401cu};
}
