#pragma once
#include <cstdint>
#include <stdexcept>

// Independently implemented register-level Hollywood IPC mailbox.
// Register bit layout: https://wiibrew.org/wiki/Hardware/IPC
// Exposes IRQ request levels, not Hollywood interrupt-controller latches or
// delivery, and does not implement IOS services or execute an ARM processor.
namespace undercover::wii {
class IpcMailbox {
public:
    enum class Side { Broadway, Starlet };
    static constexpr uint32_t PPCMSG=0, PPCCTRL=4, ARMMSG=8, ARMCTRL=12;
    static constexpr uint32_t X1=1u, Y2=2u, Y1=4u, X2=8u, IY1=16u, IY2=32u;
    static constexpr uint32_t ARM_Y1=1u, ARM_X2=2u, ARM_X1=4u, ARM_Y2=8u,
                              IX1=16u, IX2=32u;
    void reset() noexcept { *this=IpcMailbox{}; }
    uint32_t read(Side side,uint32_t offset) const {
        switch(offset){
        case PPCMSG:return ppc_message_;
        case PPCCTRL:return ppc_control();
        case ARMMSG:return arm_message_;
        case ARMCTRL:if(side==Side::Starlet)return arm_control();break;
        }
        throw std::out_of_range("Hollywood IPC invalid read offset/access");
    }
    void write(Side side,uint32_t offset,uint32_t value){
        switch(offset){
        case PPCMSG:ppc_message_=value;return;
        case PPCCTRL:
            // Broadway may clear visible X1. IOS has already observed the
            // preceding X1 assertion and must not lose its captured pointer.
            // Keep one bounded intake event separate from the MMIO flag.
            if(side==Side::Broadway&&bit(value,X1)&&!x1_&&!request_queued_){
                request_address_=ppc_message_;
                request_queued_=true;
            }
            x1_=bit(value,X1);x2_=bit(value,X2);
            if(bit(value,Y1))y1_=false;
            if(bit(value,Y2))y2_=false;
            iy1_=bit(value,IY1);iy2_=bit(value,IY2);return;
        case ARMMSG:arm_message_=value;return;
        case ARMCTRL:
            if(side!=Side::Starlet)break;
            y1_=bit(value,ARM_Y1);y2_=bit(value,ARM_Y2);
            if(bit(value,ARM_X1)){
                x1_=false;
                request_queued_=false; // IOS has acknowledged this intake.
                request_address_=0u;
            }
            if(bit(value,ARM_X2))x2_=false;
            ix1_=bit(value,IX1);ix2_=bit(value,IX2);return;
        }
        throw std::out_of_range("Hollywood IPC invalid write offset/access");
    }
    bool broadway_irq_level() const noexcept {return (y1_&&iy1_)||(y2_&&iy2_);}
    bool starlet_irq_level() const noexcept {return (x1_&&ix1_)||(x2_&&ix2_);}
    // Raw hardware state remains distinct from IOS intake. Once Broadway
    // asserts X1, its request pointer is retained until Starlet ACK even
    // if a later PPCCTRL write clears visible X1. This models a single IOS
    // request event, without automatic service or synthetic completion.
    // See WiiBrew Hardware/IPC and Dolphin's IOS request enqueue sequence.
    bool request_pending() const noexcept {return x1_;}
    // A native IOS broker rejection is not a Starlet ACK. Release only
    // this bounded intake event, leaving the readable X1 flag untouched.
    // The guest must clear/reassert X1 to submit a corrected pointer.
    void reject_invalid_ios_request() noexcept {
        request_queued_=false;
        request_address_=0u;
    }
    bool ios_request_queued() const noexcept {return request_queued_;}
    uint32_t ios_request_address() const noexcept {return request_address_;}
    bool reply_pending() const noexcept {return y1_;}
private:
    static constexpr bool bit(uint32_t value,uint32_t mask) noexcept{return (value&mask)!=0;}
    static constexpr uint32_t flag(bool value,uint32_t mask) noexcept{return value?mask:0u;}
    uint32_t ppc_control() const noexcept{
        return flag(x1_,X1)|flag(x2_,X2)|flag(y1_,Y1)|flag(y2_,Y2)|flag(iy1_,IY1)|flag(iy2_,IY2);
    }
    uint32_t arm_control() const noexcept{
        return flag(y1_,ARM_Y1)|flag(y2_,ARM_Y2)|flag(x1_,ARM_X1)|flag(x2_,ARM_X2)|flag(ix1_,IX1)|flag(ix2_,IX2);
    }
    uint32_t ppc_message_=0,arm_message_=0;
    uint32_t request_address_=0;
    bool request_queued_=false;
    bool x1_=false,x2_=false,y1_=false,y2_=false;
    bool iy1_=false,iy2_=false,ix1_=false,ix2_=false;
};
}
