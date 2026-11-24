#pragma once
#include "wii_irq_banks_v480.h"
#include <optional>
namespace undercover::wii {
// Opt-in, CPU-thread-only MMIO route for the cold interrupt banks.
// Reject unsupported widths and adjacent EXI/AI registers instead of
// letting the upstream unhandled path silently return zero.
class IrqBankBinding {
public:
    explicit IrqBankBinding(WiiIrqBanks& b):banks_(b){
        if(active_)throw std::logic_error("IRQ banks already bound");
        active_=this;
    }
    ~IrqBankBinding(){active_=nullptr;}
    IrqBankBinding(const IrqBankBinding&)=delete;
    IrqBankBinding& operator=(const IrqBankBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static void check_cpu_access(uint32_t addr,unsigned width,bool integer){
        if(!active_)return;
        const uint32_t p=addr&0x3fffffffu;
        const uint64_t end=uint64_t(p)+width;
        const auto overlaps=[&](uint32_t start,uint32_t size){return p<start+size&&end>start;};
        if(!overlaps(Mi,4)&&!overlaps(Exi,0x3c)&&!overlaps(Exi+Mirror,0x3c)&&
           !overlaps(Ai,0x10)&&!overlaps(Ai+Mirror,0x10))return;
        const auto reg=identify(addr);
        if(!integer||reg==Reg::None||reg==Reg::Unsupported||
           width!=(reg==Reg::MiMask||reg==Reg::MiStatus?2u:4u))
            throw std::runtime_error("unsupported cold IRQ bank access");
    }
    static std::optional<uint16_t> read16(uint32_t a){
        if(!active_)return std::nullopt;
        check_cpu_access(a,2,true);
        switch(identify(a)){
            case Reg::MiMask:return active_->banks_.mi_mask();
            case Reg::MiStatus:return active_->banks_.mi_status();
            default:return std::nullopt;
        }
    }
    static bool write16(uint32_t a,uint16_t value){
        if(!active_)return false;
        check_cpu_access(a,2,true);
        switch(identify(a)){
            case Reg::MiMask:active_->banks_.set_mi_mask(value);return true;
            case Reg::MiStatus:active_->banks_.clear_mi(value);return true;
            default:return false;
        }
    }
    static std::optional<uint32_t> read32(uint32_t a){
        if(!active_)return std::nullopt;
        check_cpu_access(a,4,true);
        switch(identify(a)){
            case Reg::Exi0:return active_->banks_.exi_csr(0);
            case Reg::Exi1:return active_->banks_.exi_csr(1);
            case Reg::Exi2:return active_->banks_.exi_csr(2);
            case Reg::Ai:return active_->banks_.ai_control();
            default:return std::nullopt;
        }
    }
    static bool write32(uint32_t a,uint32_t value){
        if(!active_)return false;
        check_cpu_access(a,4,true);
        switch(identify(a)){
            case Reg::Exi0:active_->banks_.write_exi_csr(0,value);return true;
            case Reg::Exi1:active_->banks_.write_exi_csr(1,value);return true;
            case Reg::Exi2:active_->banks_.write_exi_csr(2,value);return true;
            case Reg::Ai:active_->banks_.write_ai_control(value);return true;
            default:return false;
        }
    }
    static void refresh_pi(uint32_t a)noexcept{
        if(active_&&(a&0xc0000000u)!=0x40000000u&&(a&0x3fffffffu)==0x0c003000u)
            active_->banks_.refresh();
    }
private:
    enum class Reg{None,Unsupported,MiMask,MiStatus,Exi0,Exi1,Exi2,Ai};
    static constexpr uint32_t Mi=0x0c00401cu,Exi=0x0d006800u,Ai=0x0d006c00u,Mirror=0x800000u;
    WiiIrqBanks& banks_;
    inline static thread_local IrqBankBinding* active_=nullptr;
    static Reg identify(uint32_t a)noexcept{
        const bool bad=(a&0xc0000000u)==0x40000000u;
        uint32_t p=a&0x3fffffffu;
        if(p>=Mi&&p<Mi+4){
            if(bad)return Reg::Unsupported;
            return p==Mi?Reg::MiMask:p==Mi+2?Reg::MiStatus:Reg::Unsupported;
        }
        if(p>=0x0d800000u&&p<0x0d810000u)p-=Mirror;
        if(p>=Exi&&p<Exi+0x3c){
            if(bad)return Reg::Unsupported;
            return p==Exi?Reg::Exi0:p==Exi+0x14?Reg::Exi1:p==Exi+0x28?Reg::Exi2:Reg::Unsupported;
        }
        if(p>=Ai&&p<Ai+0x10)return !bad&&p==Ai?Reg::Ai:Reg::Unsupported;
        return Reg::None;
    }
};
}
