#pragma once
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <stdexcept>
#include <vector>
namespace undercover::wii {
// Translation-only overlay. Caller must authenticate owner input and
// runtime must authenticate the guest-installed copy before dispatch.
constexpr uint32_t ScSource=0x805290a8u,ScVector=0x80000c00u,ScSize=28u;
inline void add_sc_overlay(nwii::loader::Executable& exe){
    std::vector<uint8_t> image;
    for(const auto& sec:exe.sections){
        const uint64_t end=uint64_t(sec.address)+sec.data.size();
        if(sec.address<uint64_t(ScVector)+ScSize&&ScVector<end)
            throw std::runtime_error("SC translation overlay conflict");
        if(sec.is_text&&sec.address<=ScSource&&uint64_t(ScSource)+ScSize<=end){
            if(!image.empty())throw std::runtime_error("SC source ambiguous");
            const auto off=ScSource-sec.address;
            image.assign(sec.data.begin()+off,sec.data.begin()+off+ScSize);
        }
    }
    if(image.size()!=ScSize)throw std::runtime_error("SC source missing");
    for(unsigned i=0;i<ScSize;i+=4){
        const uint32_t w=(uint32_t(image[i])<<24)|(uint32_t(image[i+1])<<16)|
                         (uint32_t(image[i+2])<<8)|image[i+3];
        // No position-dependent branch, nested SC or early RFI in this
        // immutable, straight-line vector. The final instruction is RFI.
        if(i==ScSize-4){if(w!=0x4c000064u)throw std::runtime_error("SC vector return");}
        else if(w>>26==16||w>>26==18||w>>26==17||(w>>26==19&&w!=0x4c00012cu))
            throw std::runtime_error("SC vector control flow");
    }
    exe.sections.push_back({ScVector,ScSize,std::move(image),true,false});
}
}
