#pragma once
#include "wii_native_ios_transport.h"
#include <stdexcept>

namespace undercover::wii {
// Explicit thread-local bridge from the upstream MMIO wrappers to a single
// transport. The transport and its backing RAM must outlive this binding.
// Neither installing the binding nor any MMIO access schedules IOS work.
class NativeIosBinding {
public:
    explicit NativeIosBinding(NativeIosTransport& transport):transport_(transport) {
        if(active_)throw std::logic_error("native IOS transport already bound on this thread");
        active_=this;
    }
    ~NativeIosBinding(){active_=nullptr;}
    NativeIosBinding(const NativeIosBinding&)=delete;
    NativeIosBinding& operator=(const NativeIosBinding&)=delete;
    static bool active() noexcept{return active_!=nullptr;}
    // Unsupported words in the IPC window must never reach the old IOS
    // handler, even if the native bus does not implement them yet.
    static std::optional<uint32_t> read32(uint32_t address){
        if(!active_)return std::nullopt;
        if(ipc_window(address)){
            auto value=active_->transport_.read32(address);
            if(!value)throw std::runtime_error("unsupported native IOS MMIO read");
            return value;
        }
        refresh_pi(address);return std::nullopt;
    }
    static bool write32(uint32_t address,uint32_t value){
        if(!active_||!ipc_window(address))return false;
        auto& self=*active_;
        if(self.cold_phase_==1u||self.cold_phase_==2u){
            const uint32_t p=address&0x3fffffffu;
            if(self.cold_phase_!=1u||(p!=IosBus::IPC+IpcMailbox::PPCCTRL&&p!=IosBus::MIRROR+IpcMailbox::PPCCTRL)||value!=self.cold_value_){
                self.cold_phase_=4;throw std::runtime_error("unexpected cold IPC control write");
            }
        }else if(self.cold_phase_==4u)throw std::runtime_error("cold IPC proof already rejected");
        if(!self.transport_.write32(address,value))throw std::runtime_error("unsupported native IOS MMIO write");
        if(self.cold_phase_==1u)self.cold_phase_=2u;
        return true;
    }
    static void reject_subword(uint32_t address){
        if(active_&&ipc_window(address))throw std::runtime_error("subword native IOS MMIO access");
    }
    // Check the original virtual address before MMU normalization. A
    // partial access, invalid alias, or access straddling either native
    // IPC aperture must not widen, disappear, or reach legacy IOS.
    static void check_cpu_access(uint32_t address,unsigned width,bool allow_word){
        if(!active_)return;
        const uint32_t phys=address&0x3fffffffu;
        const uint64_t end=uint64_t(phys)+width;
        const auto overlaps=[&](uint32_t base){return phys<base+0x40u&&end>base;};
        if(!overlaps(IosBus::IPC)&&!overlaps(IosBus::MIRROR))return;
        if(!allow_word||width!=4u||(address&3u)||
           (address&0xc0000000u)==0x40000000u||!ipc_window(address))
            throw std::runtime_error("unsupported native IOS CPU MMIO access");
    }
    // After a legacy PI write (or before a PI read), refresh just the
    // hardware-derived Hollywood level. Preserve all other device bits.
    static void refresh_pi(uint32_t address){
        if(!active_)return;
        const uint32_t phys=address&0x3fffffffu;
        if((address&0xc0000000u)!=0x40000000u&&
           (phys==IosBus::PI_CAUSE||phys==IosBus::PI_MASK))
            (void)active_->transport_.exception_pending(0u);
    }
    // Opt-in one-shot boot IPC control proof. Captures the real backend,
    // does not fabricate mailbox state and does not service IOS.
    static bool begin_cold_control(uint32_t value){
        if(!active_)return false;
        auto& self=*active_;
        const auto s=self.transport_.cold_ipc_snapshot();
        using M=IpcMailbox;using H=HollywoodIrq;
        if(self.cold_phase_||!(value&(M::IY1|M::IY2))||(value&~0x3fu)||(value&M::X1)||
           s.queued||s.replies||s.event||(s.control&(M::X1|M::Y1|M::Y2))||
           (s.flags&H::IPC_PPC)||(s.pi_cause&s.pi_mask)){
            self.cold_phase_=4;return false;
        }
        self.cold_before_=s;self.cold_value_=value;self.cold_phase_=1;return true;
    }
    static bool finish_cold_control(){
        if(!active_)return false;
        auto& self=*active_;const auto s=self.transport_.cold_ipc_snapshot();const auto& b=self.cold_before_;
        const bool ok=self.cold_phase_==2u&&s.control==(self.cold_value_&0x39u)&&
            s.ppc==b.ppc&&s.arm==b.arm&&s.flags==b.flags&&s.irq_mask==b.irq_mask&&
            s.pi_cause==b.pi_cause&&s.pi_mask==b.pi_mask&&s.steps==b.steps&&
            !s.queued&&!s.replies&&!s.event;
        self.cold_phase_=ok?3u:4u;return ok;
    }
    // Caller owns the scheduling-boundary and CPU-exception policy.
    static std::optional<IosYieldState> service_at_guest_boundary(uint32_t msr){
        if(!active_)return std::nullopt;
        return active_->transport_.service_at_guest_boundary(msr);
    }
private:
    NativeIosTransport& transport_;
    ColdIpcSnapshot cold_before_{};
    unsigned cold_phase_=0;
    uint32_t cold_value_=0;
    inline static thread_local NativeIosBinding* active_=nullptr;
    static bool ipc_window(uint32_t a) noexcept{
        if((a&0xc0000000u)==0x40000000u)return false;
        a&=0x3fffffffu;
        return (a>=IosBus::IPC&&a<IosBus::IPC+0x40u)||
               (a>=IosBus::MIRROR&&a<IosBus::MIRROR+0x40u);
    }
};
}
