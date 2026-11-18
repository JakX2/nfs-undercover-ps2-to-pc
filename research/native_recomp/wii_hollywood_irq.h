#pragma once
#include "wii_ipc_mailbox.h"
#include <cstdint>
#include <stdexcept>

// Hollywood IRQ routing, using the publicly documented register interface:
// https://wiibrew.org/wiki/Hollywood/IRQs
// https://wiibrew.org/wiki/Hardware/IPC
// Level sampling must be called by the runtime scheduler after relevant
// mailbox transitions. No CPU exception dispatch, timing model, or
// unverified device-specific Hollywood quirks are claimed.
namespace undercover::wii {
class HollywoodIrq {
public:
    static constexpr uint32_t PPC_FLAG=0x30,PPC_MASK=0x34,ARM_FLAG=0x38,ARM_MASK=0x3c;
    static constexpr uint32_t IPC_PPC=1u<<30,IPC_ARM=1u<<31,PI_HOLLYWOOD=1u<<14;
    void reset() noexcept { *this=HollywoodIrq{}; }
    // Distinct destination latches permit devices routed to either or both
    // CPUs. The host may raise a source even while its mask is disabled.
    void raise_ppc(uint32_t flags) noexcept { ppc_flags_|=flags; }
    void raise_arm(uint32_t flags) noexcept { arm_flags_|=flags; }
    void sample_ipc(const IpcMailbox& m) noexcept {
        if(m.broadway_irq_level())raise_ppc(IPC_PPC);
        if(m.starlet_irq_level())raise_arm(IPC_ARM);
    }
    bool broadway_asserted() const noexcept { return (ppc_flags_&ppc_mask_)!=0u; }
    bool starlet_asserted() const noexcept { return (arm_flags_&arm_mask_)!=0u; }
    uint32_t pi_cause_bits() const noexcept { return broadway_asserted()?PI_HOLLYWOOD:0u; }
    uint32_t read(IpcMailbox::Side side,uint32_t reg) const {
        switch(reg){
        case PPC_FLAG:return ppc_flags_;
        case PPC_MASK:return ppc_mask_;
        case ARM_FLAG:if(side==IpcMailbox::Side::Starlet)return arm_flags_;break;
        case ARM_MASK:if(side==IpcMailbox::Side::Starlet)return arm_mask_;break;
        }
        throw std::out_of_range("unsupported Hollywood IRQ register read");
    }
    void write(IpcMailbox::Side side,uint32_t reg,uint32_t value) {
        switch(reg){
        case PPC_FLAG:ppc_flags_&=~value;return;
        case PPC_MASK:ppc_mask_=value;return;
        case ARM_FLAG:if(side==IpcMailbox::Side::Starlet){arm_flags_&=~value;return;}break;
        case ARM_MASK:if(side==IpcMailbox::Side::Starlet){arm_mask_=value;return;}break;
        }
        throw std::out_of_range("unsupported Hollywood IRQ register write");
    }
private:
    uint32_t ppc_flags_=0,ppc_mask_=0,arm_flags_=0,arm_mask_=0;
};
}
