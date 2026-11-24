#pragma once
#include "wii_ios_memory.h"
#include <algorithm>
#include <cstddef>
#include <span>
#include <stdexcept>

namespace undercover::wii {
// Non-owning physical RAM view. The host must keep both spans alive and
// stable for the lifetime of the IOS transport. NWiiRuntime's extra eight
// bytes of read padding are deliberately excluded from IOS memory.
class WiiPhysicalRam final : public IosMemory {
public:
    static constexpr uint32_t MEM1_SIZE=24u*1024u*1024u;
    static constexpr uint32_t MEM2_BASE=0x10000000u;
    static constexpr uint32_t MEM2_SIZE=64u*1024u*1024u;
    WiiPhysicalRam(std::span<uint8_t> mem1,std::span<uint8_t> mem2) noexcept
        :mem1_(mem1.first(std::min(mem1.size(),std::size_t(MEM1_SIZE)))),
         mem2_(mem2.first(std::min(mem2.size(),std::size_t(MEM2_SIZE)))){}
    bool valid(uint32_t a,uint32_t n) const override {
        if(!n)return false;
        if(a<MEM1_SIZE)return uint64_t(a)+n<=mem1_.size();
        if(a>=MEM2_BASE&&a-MEM2_BASE<MEM2_SIZE)
            return uint64_t(a-MEM2_BASE)+n<=mem2_.size();
        return false;
    }
    uint8_t read8(uint32_t a) const override{return *byte(a);}
    void write8(uint32_t a,uint8_t v) override{*byte(a)=v;}
private:
    std::span<uint8_t> mem1_,mem2_;
    uint8_t* byte(uint32_t a) const {
        if(!valid(a,1u))throw std::out_of_range("IOS physical RAM address");
        return a<MEM1_SIZE?mem1_.data()+a:mem2_.data()+(a-MEM2_BASE);
    }
};
}
