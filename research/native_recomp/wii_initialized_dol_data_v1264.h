#pragma once
#include <algorithm>
#include <cstdint>
#include <fstream>
#include <span>
#include <stdexcept>
#include <vector>

namespace undercover::wii {
struct InitializedDolRange{uint32_t file,address,size;};
// Only initialized DOL data (never text or BSS). The caller has already
// authenticated the same owner DOL before generating any native code.
inline std::vector<InitializedDolRange> initialized_dol_ranges(std::span<const uint8_t> raw){
    if(raw.size()<256u||raw.size()>32u*1024u*1024u)throw std::runtime_error("DOL data size");
    const auto be=[&](unsigned a){
        return (uint32_t(raw[a])<<24)|(uint32_t(raw[a+1])<<16)|(uint32_t(raw[a+2])<<8)|raw[a+3];
    };
    std::vector<InitializedDolRange> ranges;
    for(unsigned i=0;i<11;++i){
        const uint32_t off=be(0x1cu+4u*i),addr=be(0x64u+4u*i),n=be(0xacu+4u*i);
        if(!n)continue;
        if(off<256u||uint64_t(off)+n>raw.size()||addr<0x80004000u||
           uint64_t(addr)+n>0x81800000ull)throw std::runtime_error("DOL data geometry");
        for(const auto& x:ranges){
            if((addr<uint64_t(x.address)+x.size&&x.address<uint64_t(addr)+n)||
               (off<uint64_t(x.file)+x.size&&x.file<uint64_t(off)+n))
                throw std::runtime_error("DOL data overlap");
        }
        ranges.push_back({off,addr,n});
    }
    if(ranges.empty())throw std::runtime_error("DOL data missing");
    return ranges;
}
template<class M>void seed_initialized_dol_data(M& mmu,std::span<const uint8_t> raw){
    const auto ranges=initialized_dol_ranges(raw);
    // Validate every destination before copying even one byte.
    std::vector<uint8_t*> dest;
    for(const auto& x:ranges){
        auto* p=mmu.get_ptr(x.address);auto* q=mmu.get_ptr(x.address+x.size-1u);
        if(!p||!q||reinterpret_cast<uintptr_t>(q)<reinterpret_cast<uintptr_t>(p)||
           reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)!=x.size-1u)
            throw std::runtime_error("DOL data destination");
        dest.push_back(p);
    }
    for(unsigned i=0;i<ranges.size();++i){
        const auto& x=ranges[i];std::copy_n(raw.data()+x.file,x.size,dest[i]);
    }
}
inline std::vector<uint8_t> read_initialized_dol_input(const char* path){
    std::ifstream f(path,std::ios::binary|std::ios::ate);
    if(!f)throw std::runtime_error("DOL data input");
    const auto size=f.tellg();
    if(size<256||size>32*1024*1024)throw std::runtime_error("DOL data size");
    std::vector<uint8_t> raw(static_cast<size_t>(size));
    f.seekg(0);f.read(reinterpret_cast<char*>(raw.data()),static_cast<std::streamsize>(size));
    if(!f)throw std::runtime_error("DOL data input");
    (void)initialized_dol_ranges(raw);return raw;
}
}
