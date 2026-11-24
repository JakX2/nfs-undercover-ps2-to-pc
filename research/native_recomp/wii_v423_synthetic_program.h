#pragma once
#include <array>
#include <cstdint>
#include <cstddef>

// Independently authored PPC program; no original game instruction bytes.
namespace undercover::wii::v423 {
inline constexpr uint32_t Entry=0x80004000u,Vector=0x80000500u;
constexpr uint32_t d(unsigned op,unsigned rt,unsigned ra,unsigned imm){return (op<<26)|(rt<<21)|(ra<<16)|(imm&0xffffu);}
constexpr uint32_t spr(unsigned n,unsigned reg,bool write){return (31u<<26)|(reg<<21)|(((n&31u)<<5)|(n>>5))<<11|((write?467u:339u)<<1);}
inline constexpr std::array<uint32_t,14> Main{
    d(15,8,0,0xcd00),d(15,9,0,0xcd80),d(15,10,0,0x4000),d(14,11,0,0x100),
    d(36,10,9,0x34),d(36,11,8,0),d(14,12,0,0x31),d(36,12,8,4),
    d(14,4,0,0),d(24,4,4,0x8000),(31u<<26)|(4u<<21)|(146u<<1),
    d(14,5,5,1),0x44000002u,0x4e800020u
};
inline constexpr uint32_t Resume=Entry+11u*4u,Stop=Entry+12u*4u;
// Guest reads live Y flags and performs BOTH W1C writes. r14 is restored
// via SPRG0; r6 deliberately counts completed handler bodies.
inline constexpr std::array<uint32_t,7> Handler{
    spr(272,14,true),d(32,14,8,4),d(36,14,8,4),d(36,10,9,0x30),
    spr(272,14,false),d(14,6,6,1),0x4c000064u
};
template<std::size_t N> constexpr auto bytes(const std::array<uint32_t,N>& words){
    std::array<uint8_t,N*4> out{};
    for(std::size_t i=0;i<N;++i)for(unsigned k=0;k<4;++k)out[i*4+k]=uint8_t(words[i]>>(24-8*k));
    return out;
}
inline constexpr auto MainBytes=bytes(Main);
inline constexpr auto VectorBytes=bytes(Handler);
}
