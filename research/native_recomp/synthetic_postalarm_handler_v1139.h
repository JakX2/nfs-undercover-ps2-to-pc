#pragma once
#include "wii_handler_suffix_guard_v868.h"
#include "wii_handler_index_branch_v911.h"
namespace undercover::wii::v1139 {
inline constexpr uint32_t A=0x80004030u,Table=0x8000f000u,Nop=0x60000000u;
inline constexpr uint32_t rd=A+4u,wr=A+8u,Rd=0x80830038u,Wr=0x90830038u;
inline constexpr uint32_t Indexed=(31u<<26)|(5u<<21)|(3u<<16)|(4u<<11)|(23u<<1);
inline constexpr uint32_t Compare=(10u<<26)|(5u<<16)|7u,Branch=(16u<<26)|(12u<<21)|(2u<<16)|12u;
inline constexpr HandlerIndexBranchExpectation index{A,Indexed,Compare,Branch,A+64u,
    {Table,Table+4u,Table+8u,Table+12u},20u};
inline constexpr std::array<HandlerSuffixLabel,16> rows=[]{
    std::array<HandlerSuffixLabel,16> r{};
    for(unsigned i=0;i<14;++i)r[i]={A+4u*i,Nop,0,0};
    r[1].word=Rd;r[2].word=Wr;r[11].word=Indexed;r[12].word=Compare;r[13].word=Branch;
    r[14]={A+56u,0x48000008u,0,0};r[15]={A+64u,0x48000041u,12u,1u};return r;
}();
}
