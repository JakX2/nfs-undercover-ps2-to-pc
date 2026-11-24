#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <stdexcept>
namespace undercover::wii {
// Register-level Wii IRQ banks, deliberately not a device or transfer model.
// Public register maps:
// https://wiibrew.org/wiki/Hardware/Memory_Interface
// https://wiibrew.org/wiki/Hardware/External_Interface
// https://wiibrew.org/wiki/Hardware/Audio_Interface
// https://wiibrew.org/wiki/Hardware/Processor_Interface
// One CPU-thread owner. The atomics are shared with the PI backend.
class WiiIrqBanks {
public:
    static constexpr uint32_t PI_EXI=1u<<4,PI_AI=1u<<5,PI_MI=1u<<7;
    static constexpr uint16_t MI_BITS=0x1fu;
    static constexpr uint32_t EXI_INT=2u,TC_INT=8u,EXT_INT=0x800u,EXT=0x1000u;
    static constexpr uint32_t AI_MASK=4u,AI_INT=8u;
    explicit WiiIrqBanks(std::atomic<uint32_t>& pi):pi_(pi){refresh();}
    WiiIrqBanks(const WiiIrqBanks&)=delete;
    WiiIrqBanks& operator=(const WiiIrqBanks&)=delete;
    // The memory subsystem must explicitly raise a protection event.
    void raise_mi(uint16_t bits){if(bits&~MI_BITS)throw std::invalid_argument("MI source");mi_status_|=bits;refresh();}
    void set_mi_mask(uint16_t bits){mi_mask_=bits&MI_BITS;refresh();}
    void clear_mi(uint16_t bits){mi_status_&=~(bits&MI_BITS);refresh();}
    uint16_t mi_mask()const noexcept{return mi_mask_;}
    uint16_t mi_status()const noexcept{return mi_status_;}
    // Explicit cold protection-register profile, no memory permissions.
    void enable_mi_boot(){if(mi_boot_)throw std::logic_error("MI boot already enabled");mi_boot_=true;}
    bool mi_boot()const noexcept{return mi_boot_;}
    unsigned mi_boot_stage()const noexcept{return mi_stage_;}
    uint16_t mi_protection()const noexcept{return mi_protection_;}
    uint16_t mi_aux()const noexcept{return mi_aux_;}
    void write_mi_aux(uint16_t v){
        if(!mi_boot_||mi_stage_!=0||v!=0)throw std::runtime_error("unsupported MI cold auxiliary write");
        mi_aux_=v;++mi_stage_;
    }
    void write_mi_protection(uint16_t v){
        if(!mi_boot_||mi_stage_!=1||v!=255)throw std::runtime_error("unsupported MI cold protection write");
        mi_protection_=v;++mi_stage_;
    }
    // EXI status is distinct from interrupt enable and chip select.
    // Only the device/backend may assert a status event.
    void raise_exi(unsigned ch,uint32_t bits){
        auto& s=channel(ch);
        if(bits&~status_bits(ch))throw std::invalid_argument("EXI source");
        s.status|=bits;refresh();
    }
    void presence(unsigned ch,bool present){
        if(ch>1)throw std::invalid_argument("EXI external slot");
        auto& s=channel(ch);
        if(s.present!=present){s.present=present;s.status|=EXT_INT;refresh();}
    }
    uint32_t exi_csr(unsigned ch)const{
        auto& s=channel(ch);return s.control|s.status|(s.present?EXT:0u);
    }
    void write_exi_csr(unsigned ch,uint32_t value){
        auto& s=channel(ch);
        // Wii ROMDIS behavior is not implemented; reserved bits cannot
        // accidentally start another operation. EXT is read-only.
        if(value&~(control_bits(ch)|status_bits(ch)|(ch<2?EXT:0u)))
            throw std::runtime_error("unsupported EXI CSR bits");
        s.control=value&control_bits(ch);
        s.status&=~(value&status_bits(ch));
        refresh();
    }
    // Only stopped audio-interface control is supported here. The audio
    // clock, streaming, DMA and sample counter are separate responsibilities.
    uint32_t ai_control()const noexcept{return ai_control_|ai_status_;}
    void write_ai_control(uint32_t value){
        if(value&~0x7fu||value&1u)throw std::runtime_error("unsupported active Wii AI");
        ai_status_&=~(value&AI_INT);
        // Counter reset is a command, not persistent state. No samples
        // advance in this cold-start register-only model.
        ai_control_=value&0x56u;
        refresh();
    }
    void raise_ai(){ai_status_|=AI_INT;refresh();}
    void refresh()noexcept{
        bool exi=false;
        for(unsigned ch=0;ch<3;++ch){
            const auto& s=exi_[ch];
            exi|=(s.status&(s.control<<1)&status_bits(ch))!=0;
        }
        constexpr uint32_t owned=PI_MI|PI_EXI|PI_AI;
        const uint32_t desired=(mi_mask_&mi_status_?PI_MI:0u)|(exi?PI_EXI:0u)|
            ((ai_control_&AI_MASK)&&(ai_status_&AI_INT)?PI_AI:0u);
        // Preserve concurrent non-owned PI sources, including Hollywood.
        auto current=pi_.load(std::memory_order_relaxed);
        while(!pi_.compare_exchange_weak(current,(current&~owned)|desired,
               std::memory_order_relaxed,std::memory_order_relaxed)){}
    }
private:
    struct Channel{uint32_t control=0,status=0;bool present=false;};
    std::array<Channel,3> exi_{};uint16_t mi_mask_=0,mi_status_=0;
    uint32_t ai_control_=0,ai_status_=0;
    std::atomic<uint32_t>& pi_;
    static constexpr uint32_t control_bits(unsigned ch){return 0x3f5u|(ch<2?0x400u:0u);}
    static constexpr uint32_t status_bits(unsigned ch){return EXI_INT|TC_INT|(ch<2?EXT_INT:0u);}
    Channel& channel(unsigned ch){if(ch>=3)throw std::out_of_range("EXI channel");return exi_[ch];}
    const Channel& channel(unsigned ch)const{if(ch>=3)throw std::out_of_range("EXI channel");return exi_[ch];}
};
}
