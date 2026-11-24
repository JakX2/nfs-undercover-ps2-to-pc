#pragma once
#include <array>
#include <cstdint>
#include <optional>
#include <stdexcept>
namespace undercover::wii {
// Hollywood register names and addresses: WiiBrew Hollywood/Registers.
// This subset preserves the observed cold audio bootstrap RMW fields only.
// No PLL lock, clock switching, AI/DSP service, power or timing is modeled.
class AudioAcrBinding {
public:
    struct Profile{uint32_t compat,pll,ext;};
    static constexpr uint32_t Compat=0x0d800180u,Pll=0x0d8001ccu,Ext=0x0d8001d0u;
    explicit AudioAcrBinding(Profile profile):values_{profile.compat,profile.pll,profile.ext}{
        if(active_)throw std::logic_error("audio ACR already bound");
        active_=this;
    }
    ~AudioAcrBinding(){active_=nullptr;}
    AudioAcrBinding(const AudioAcrBinding&)=delete;
    AudioAcrBinding& operator=(const AudioAcrBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static void check(uint32_t address,unsigned width,bool integer){
        if(!active_)return;
        const auto p=address&0x3fffffffu;
        for(auto base:Addresses){
            if(p>=base+4u||uint64_t(p)+width<=base)continue;
            if(p!=base||width!=4u||!integer||(address&0xc0000000u)==0x40000000u)
                throw std::runtime_error("audio ACR access");
            return;
        }
    }
    static std::optional<uint32_t> read32(uint32_t address){
        if(!active_)return std::nullopt;
        check(address,4,true);const auto i=index(address);
        return i?std::optional<uint32_t>(active_->values_[*i]):std::nullopt;
    }
    static bool write32(uint32_t address,uint32_t value){
        if(!active_)return false;
        check(address,4,true);const auto i=index(address);if(!i)return false;
        auto& previous=active_->values_[*i];
        if((previous^value)&~Writable[*i])throw std::runtime_error("audio ACR unsupported bit change");
        previous=value;return true;
    }
private:
    static constexpr std::array<uint32_t,3> Addresses{Compat,Pll,Ext};
    // Observed guest-modified fields, not a complete hardware writable mask.
    static constexpr std::array<uint32_t,3> Writable{0x180u,0x07ffffffu,0xd0000000u};
    static std::optional<unsigned> index(uint32_t a)noexcept{
        const uint32_t p=a&0x3fffffffu;
        for(unsigned i=0;i<Addresses.size();++i)if(p==Addresses[i])return i;
        return std::nullopt;
    }
    std::array<uint32_t,3> values_;
    inline static thread_local AudioAcrBinding* active_=nullptr;
};
}
