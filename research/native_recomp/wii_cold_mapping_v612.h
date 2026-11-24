#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Explicit bounded boot profile matching the V65/V67 owner mapping lane.
// Physical MEM2 capacity is 64 MiB; this cold profile's mapped high is
// 0x93400000, with the final 512 KiB reserved for IPC. Do not conflate
// capacity with the guest's usable mapped address range.
struct ColdMappingProfile {
    struct Field {uint32_t addr,prior,value;};
    static constexpr std::array<Field,9> Fields{{
        {0x80003100u,0,0x01800000u},{0x80003104u,0,0x01800000u},
        {0x80003118u,0x04000000u,0x04000000u},{0x8000311cu,0x04000000u,0x04000000u},
        {0x80003120u,0,0x93400000u},{0x80003124u,0x90000800u,0x90000800u},
        {0x80003128u,0x93e00000u,0x93380000u},{0x80003130u,0x93e00000u,0x93380000u},
        {0x80003134u,0x94000000u,0x93400000u}
    }};
    template<class Mmu,class Sections>
    static bool install(Mmu& m,const Sections& sections,bool wii,bool dol_only){
        if(!wii||!dol_only)return false;
        // Preflight all words and initialized section overlaps before writing.
        // A BSS declaration is not an initialized byte owner.
        for(auto f:Fields){
            if(!m.get_ptr(f.addr)||!m.get_ptr(f.addr+3u)||m.read32(f.addr)!=f.prior)return false;
            for(const auto& s:sections)
                if(!s.is_bss&&s.size&&uint64_t(f.addr)<uint64_t(s.address)+s.size&&
                   uint64_t(s.address)<uint64_t(f.addr)+4u)return false;
        }
        for(auto f:Fields)if(f.value!=f.prior)m.write32(f.addr,f.value);
        for(auto f:Fields)if(m.read32(f.addr)!=f.value)return false;
        return true;
    }
};
}
