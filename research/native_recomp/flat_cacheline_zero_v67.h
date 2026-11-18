#pragma once
// Original-free flat-RAM semantics of PPC dcbz. No cache residency, locked
// cache, permission, or MMIO emulation. Invalid or non-RAM blocks fail closed.
#include <cstdint>
#include <cstring>
#include <stdexcept>
namespace nwii::runtime {
struct FlatCachelineZeroTrace {
    uint64_t count=0;
    uint32_t first=0,last=0;
    void clear(){*this={};}
    template<class Mmu> void zero(Mmu& mmu,uint32_t ea){
        const uint32_t line=ea&~31u;
        auto* start=mmu.get_ptr(line);
        auto* end=mmu.get_ptr(line+31u);
        if(!start||!end||end!=start+31u)
            throw std::runtime_error("dcbz requires complete contiguous guest RAM cache line");
        std::memset(start,0,32);
        if(count==0)first=line;
        last=line;++count;
    }
};
}
