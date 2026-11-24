#pragma once
#include <cstdint>
#include <optional>
#include <stdexcept>
namespace undercover::wii {
// Cold VI clock selection only. YAGCD §5.3 VICLK (0xCC00206C):
// 0 selects 27 MHz, 1 selects 54 MHz. This does not generate VI timing,
// retraces, interrupts or a framebuffer. No implicit boot profile.
class ViClockBinding {
public:
    explicit ViClockBinding(uint16_t clock):clock_(clock){
        if(clock>1u)throw std::invalid_argument("VI clock value");
        if(active_)throw std::logic_error("VI clock already bound");
        active_=this;
    }
    ~ViClockBinding(){active_=nullptr;}
    ViClockBinding(const ViClockBinding&)=delete;
    ViClockBinding& operator=(const ViClockBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static std::optional<uint16_t> selected()noexcept{
        return active_?std::optional<uint16_t>(active_->clock_):std::nullopt;
    }
    static void check(uint32_t addr,unsigned width,bool integer){
        if(!active_)return;
        const auto p=addr&0x3fffffffu;
        if(p>=Base+2u||uint64_t(p)+width<=Base)return;
        if(p!=Base||width!=2u||!integer||(addr&0xc0000000u)==0x40000000u)
            throw std::runtime_error("VI clock access");
    }
    static std::optional<uint16_t> read16(uint32_t addr){
        if(!active_)return std::nullopt;
        check(addr,2,true);
        if((addr&0x3fffffffu)!=Base)return std::nullopt;
        return active_->clock_;
    }
    static bool write16(uint32_t addr,uint16_t value){
        if(!active_)return false;
        check(addr,2,true);
        if((addr&0x3fffffffu)!=Base)return false;
        if(value>1u)throw std::runtime_error("VI clock reserved bits");
        active_->clock_=value;return true;
    }
private:
    static constexpr uint32_t Base=0x0c00206cu;
    uint16_t clock_;
    inline static thread_local ViClockBinding* active_=nullptr;
};
}
