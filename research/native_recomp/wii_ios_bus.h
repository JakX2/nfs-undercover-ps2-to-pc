#pragma once
#include "wii_stm_ios.h"
#include "wii_hollywood_irq.h"
#include <cstdint>
#include <optional>

// Native Broadway-facing IPC + Hollywood + Processor Interface register
// integration. Explicit host scheduler steps, never synchronous MMIO return
// fabrication. Public specs:
// https://wiibrew.org/wiki/Hardware/IPC
// https://wiibrew.org/wiki/Hollywood/IRQs
// https://wiibrew.org/wiki/Hardware/Processor_Interface
namespace undercover::wii {
class IosBus {
public:
    static constexpr uint32_t IPC=0x0d000000u, MIRROR=0x0d800000u;
    static constexpr uint32_t PI_CAUSE=0x0c003000u, PI_MASK=0x0c003004u;
    static constexpr uint32_t MSR_EE=0x8000u;
    explicit IosBus(IosMemory& memory):ios_(mail_,memory){}
    IosBus(const IosBus&)=delete;
    IosBus& operator=(const IosBus&)=delete;
    void reset() noexcept {
        ios_.reset();mail_.reset();irq_.reset();pi_mask_=other_causes_=0u;
    }
    StmIos& services() noexcept{return ios_;}
    // Additional PI devices own their causes; Hollywood bit is derived.
    void set_other_pi_causes(uint32_t causes) noexcept {
        other_causes_=causes&~HollywoodIrq::PI_HOLLYWOOD;
    }
    uint32_t pi_cause() const noexcept {return other_causes_|irq_.pi_cause_bits();}
    bool external_irq_level() const noexcept {return (pi_cause()&pi_mask_)!=0u;}
    bool external_exception_pending(uint32_t msr) const noexcept {
        return (msr&MSR_EE)!=0u&&external_irq_level();
    }
    // Return nullopt/false for unsupported addresses so the platform's
    // other MMIO devices retain ownership; reject unaligned access.
    std::optional<uint32_t> read32(uint32_t address) const {
        if(address&3u)return std::nullopt;
        if(address==PI_CAUSE)return pi_cause();
        if(address==PI_MASK)return pi_mask_;
        const auto r=offset(address);
        if(!r)return std::nullopt;
        using M=IpcMailbox;using H=HollywoodIrq;
        constexpr auto P=M::Side::Broadway;
        switch(*r){
        case M::PPCMSG:case M::PPCCTRL:case M::ARMMSG:return mail_.read(P,*r);
        case H::PPC_FLAG:case H::PPC_MASK:return irq_.read(P,*r);
        default:return std::nullopt;
        }
    }
    bool write32(uint32_t address,uint32_t value) {
        if(address&3u)return false;
        if(address==PI_MASK){pi_mask_=value;return true;}
        const auto r=offset(address);
        if(!r)return false;
        using M=IpcMailbox;using H=HollywoodIrq;
        constexpr auto P=M::Side::Broadway;
        switch(*r){
        case M::PPCMSG:case M::PPCCTRL:case M::ARMMSG:
            mail_.write(P,*r,value);irq_.sample_ipc(mail_);return true;
        case H::PPC_FLAG:case H::PPC_MASK:
            irq_.write(P,*r,value);irq_.sample_ipc(mail_);return true;
        default:return false;
        }
    }
    StmIos::Pump tick() {
        const auto result=ios_.pump();
        irq_.sample_ipc(mail_);
        return result;
    }
private:
    IpcMailbox mail_;
    HollywoodIrq irq_;
    StmIos ios_;
    uint32_t pi_mask_=0,other_causes_=0;
    static std::optional<uint32_t> offset(uint32_t a){
        if(a>=IPC&&a<IPC+0x40u)return a-IPC;
        if(a>=MIRROR&&a<MIRROR+0x40u)return a-MIRROR;
        return std::nullopt;
    }
};
}
