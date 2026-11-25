#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
namespace undercover::wii {
// Classification only: neither guest memory nor CTR is written. All
// candidate words are privately authenticated by the installer.
template<class C,std::size_t N>
unsigned classify_callback_identity(C& c,uint32_t pc,uint32_t w,unsigned ordinal,
    unsigned kind,uint32_t candidate,const std::array<uint32_t,N>& words,
    const std::array<uint32_t,2>& sites){
    static_assert(N>=1&&N<=1024);
    if(kind!=2u||w!=0x4e800421u||
       !((ordinal==6u&&pc==sites[0])||(ordinal==11u&&pc==sites[1])))return 0u;
    const uint32_t target=uint32_t(c.ctr)&~3u;
    auto mapped=[&](uint32_t a){
        return a>=0x80000000u&&a<=0x817ffffcu&&
            c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);
    };
    if(!mapped(target))return 3u;
    if(target!=candidate)return 1u;
    if(uint64_t(target)+4u*N>0x81800000ull)return 3u;
    for(std::size_t i=1;i<N;++i)if(!mapped(target+uint32_t(4u*i)))return 3u;
    for(std::size_t i=0;i<N;++i)
        if(c.mmu.read32(target+uint32_t(4u*i))!=words[i])return 4u;
    return 2u;
}
}
