#pragma once
#include "wii_dsp_control_v554.h"
#include <optional>
namespace undercover::wii {
// Exclusive, explicit test owner for the ARAM-only DSP aperture. A full
// DSP controller must merge reset/mailbox/audio status before activation
// in the original game. Unsupported registers never reach legacy DSP.
class AramBinding {
public:
    static constexpr uint32_t Base=0x0c005000u,Control=0xau,Info=0x12u,Main=0x20u,Aux=0x24u,Count=0x28u;
    explicit AramBinding(AramDma& dma):dma_(dma){
        if(active_)throw std::logic_error("ARAM binding already active");
        active_=this;
    }
    AramBinding(AramDma& dma,DspControl& dsp):dma_(dma),dsp_(&dsp){
        if(active_||!dsp.owns(dma))throw std::logic_error("DSP binding ownership");
        active_=this;
    }
    ~AramBinding(){active_=nullptr;}
    AramBinding(const AramBinding&)=delete;
    AramBinding& operator=(const AramBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static void check(uint32_t a,unsigned width,bool integer){
        if(!active_)return;
        const auto p=a&0x3fffffffu;
        if(p>=Base+(active_->dsp_?0x200u:0x3cu)||uint64_t(p)+width<=Base)return;
        auto off=offset(a);
        if(!integer||!off||width!=size(*off,active_->dsp_!=nullptr))throw std::runtime_error("unsupported ARAM MMIO access");
    }
    static std::optional<uint16_t> read16(uint32_t a){
        if(!active_)return std::nullopt;
        check(a,2,true);auto off=offset(a);if(!off)return std::nullopt;
        if(auto dsp=active_->dsp_){
            switch(*off){case 0:return dsp->cpu_high();case 2:return dsp->cpu_low();
            case 4:return dsp->dsp_high();case 6:return dsp->dsp_read_low();
            case Control:return dsp->read_control();}
        }
        return *off==Control?active_->dma_.control_bits():active_->dma_.info();
    }
    static bool write16(uint32_t a,uint16_t v){
        if(!active_)return false;
        check(a,2,true);auto off=offset(a);if(!off)return false;
        if(auto dsp=active_->dsp_){
            switch(*off){case 0:dsp->cpu_write_high(v);return true;
            case 2:dsp->cpu_write_low(v);return true;
            case 4:case 6:throw std::runtime_error("DSP outbound mailbox is read-only to PPC");
            case Control:dsp->write_control(v);return true;}
        }
        if(*off==Control)active_->dma_.write_irq_control(v);else active_->dma_.set_info(v);
        return true;
    }
    static std::optional<uint32_t> read32(uint32_t a){
        if(!active_)return std::nullopt;
        check(a,4,true);auto off=offset(a);if(!off)return std::nullopt;
        switch(*off){case Main:return active_->dma_.main_address();case Aux:return active_->dma_.aram_address();case Count:return active_->dma_.count();}
        throw std::logic_error("ARAM register dispatch");
    }
    static bool write32(uint32_t a,uint32_t v){
        if(!active_)return false;
        check(a,4,true);auto off=offset(a);if(!off)return false;
        switch(*off){case Main:active_->dma_.set_main_address(v);break;case Aux:active_->dma_.set_aram_address(v);break;case Count:active_->dma_.start(v);break;default:throw std::logic_error("ARAM register dispatch");}
        return true;
    }
    static void advance(uint64_t tick){if(active_)active_->dma_.advance(tick);}
    static void refresh_pi(uint32_t a)noexcept{
        if(active_&&(a&0xc0000000u)!=0x40000000u&&(a&0x3fffffffu)==0x0c003000u)
            active_->dma_.refresh();
    }
private:
    AramDma& dma_;DspControl* dsp_=nullptr;inline static thread_local AramBinding* active_=nullptr;
    static unsigned size(unsigned off,bool dsp)noexcept{
        if(dsp&&(off==0||off==2||off==4||off==6))return 2;
        return off==Control||off==Info?2u:off==Main||off==Aux||off==Count?4u:0u;
    }
    static std::optional<unsigned> offset(uint32_t a)noexcept{
        auto p=a&0x3fffffffu;
        if((a&0xc0000000u)==0x40000000u||p<Base||p>=Base+(active_->dsp_?0x200u:0x3cu))return std::nullopt;
        return p-Base;
    }
};
}
