#pragma once
#include "wii_si_controller_v511.h"
namespace undercover::wii {
// CPU-thread-only SI MMIO route. Native Wii aperture and Hollywood mirror;
// the GameCube aperture is intentionally not treated as a Wii SI alias.
class SiBinding {
public:
    explicit SiBinding(SiController& controller):controller_(controller){
        if(active_)throw std::logic_error("SI already bound");
        active_=this;
    }
    ~SiBinding(){active_=nullptr;}
    SiBinding(const SiBinding&)=delete;
    SiBinding& operator=(const SiBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static bool owns(const SiController& controller)noexcept{return active_ && &active_->controller_==&controller;}
    static void check(uint32_t addr,unsigned width,bool integer){
        if(!active_)return;
        const auto p=addr&0x3fffffffu;
        const auto end=uint64_t(p)+width;
        const auto overlap=[&](uint32_t base){return p<base+0x100u&&end>base;};
        if(!overlap(Base)&&!overlap(Base+Mirror))return;
        const auto off=offset(addr);
        if(width!=4||!integer||!off||!SiController::supported(*off))
            throw std::runtime_error("SI unsupported access");
    }
    static std::optional<uint32_t> read32(uint32_t a){
        if(!active_)return std::nullopt;
        check(a,4,true);const auto off=offset(a);
        if(!off)return std::nullopt;
        return active_->controller_.read(*off);
    }
    static bool write32(uint32_t a,uint32_t value){
        if(!active_)return false;
        check(a,4,true);const auto off=offset(a);
        if(!off)return false;
        active_->controller_.write(*off,value);return true;
    }
    static void refresh_pi(uint32_t a)noexcept{
        if(active_&&(a&0xc0000000u)!=0x40000000u&&(a&0x3fffffffu)==0x0c003000u)
            active_->controller_.refresh();
    }
private:
    static constexpr uint32_t Base=0x0d006400u,Mirror=0x00800000u;
    static std::optional<unsigned> offset(uint32_t a)noexcept{
        if((a&0xc0000000u)==0x40000000u)return std::nullopt;
        const auto p=(a&0x3fffffffu)&~Mirror;
        if(p<Base||p>=Base+0x100u)return std::nullopt;
        return p-Base;
    }
    SiController& controller_;inline static thread_local SiBinding* active_=nullptr;
};
}
