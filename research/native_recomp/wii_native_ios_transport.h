#pragma once
#include "wii_physical_ram.h"
#include "wii_ios_yield_scheduler.h"
#include <atomic>
#include <optional>

namespace undercover::wii {
// Opt-in host boundary for one Broadway CPU/MMU lifetime. No legacy IOS
// fallback for owned registers, no synchronous servicing on an MMIO write,
// and no CPU exception or fabricated guest result. Other PI device bits
// remain owned by their existing runtime producers.
class NativeIosTransport {
public:
    NativeIosTransport(std::span<uint8_t> mem1,std::span<uint8_t> mem2,
                       std::atomic<uint32_t>& pi_cause,std::atomic<uint32_t>& pi_mask)
        :ram_(mem1,mem2),bus_(ram_),scheduler_(bus_),cause_(pi_cause),mask_(pi_mask){sync();}
    NativeIosTransport(const NativeIosTransport&)=delete;
    NativeIosTransport& operator=(const NativeIosTransport&)=delete;
    // Recognize the physical register and its cached/uncached aliases only.
    // Unaligned/subword access to owned registers must not reach legacy IOS.
    static bool owns_byte(uint32_t a) noexcept{return normalized(a&~3u).has_value();}
    std::optional<uint32_t> read32(uint32_t a) {
        const auto reg=normalized(a);if(!reg)return std::nullopt;
        sync();return bus_.read32(*reg);
    }
    bool write32(uint32_t a,uint32_t value) {
        const auto reg=normalized(a);if(!reg)return false;
        sync();const bool ok=bus_.write32(*reg,value);publish();return ok;
    }
    // Called at a separately authenticated guest scheduling boundary, not
    // on MMIO. Only one actual queued request/reply may advance per call.
    std::optional<IosYieldState> service_at_guest_boundary(uint32_t msr) {
        sync();
        if(!bus_.pending_native_ios_request()&&!bus_.services().queued_replies())return std::nullopt;
        const auto state=scheduler_.service_one(msr);publish();return state;
    }
    // The host PI mask can change outside this transport (e.g. OS IRQ code).
    bool exception_pending(uint32_t msr) {sync();return bus_.external_exception_pending(msr);}
    StmIos& services() noexcept{return bus_.services();}
    WiiPhysicalRam& physical_ram() noexcept{return ram_;}
    uint64_t serviced_steps() const noexcept{return scheduler_.serviced_steps();}
private:
    WiiPhysicalRam ram_;
    IosBus bus_;
    IosYieldScheduler scheduler_;
    std::atomic<uint32_t>& cause_;
    std::atomic<uint32_t>& mask_;
    static std::optional<uint32_t> normalized(uint32_t a) noexcept {
        if((a&3u)||(a&0xc0000000u)==0x40000000u)return std::nullopt;
        a&=0x3fffffffu;
        uint32_t off;
        if(a>=IosBus::IPC&&a<IosBus::IPC+0x40u)off=a-IosBus::IPC;
        else if(a>=IosBus::MIRROR&&a<IosBus::MIRROR+0x40u)off=a-IosBus::MIRROR;
        else return std::nullopt;
        using M=IpcMailbox;using H=HollywoodIrq;
        switch(off){case M::PPCMSG:case M::PPCCTRL:case M::ARMMSG:
            case H::PPC_FLAG:case H::PPC_MASK:return a;
            default:return std::nullopt;}
    }
    void sync() {
        bus_.set_other_pi_causes(cause_.load(std::memory_order_relaxed));
        bus_.write32(IosBus::PI_MASK,mask_.load(std::memory_order_relaxed));
        // Reassert the derived level if a PI-side W1C cleared it before
        // the original guest cleared the Hollywood source latch.
        publish();
    }
    void publish() noexcept {
        constexpr uint32_t bit=HollywoodIrq::PI_HOLLYWOOD;
        if(bus_.pi_cause()&bit)cause_.fetch_or(bit,std::memory_order_relaxed);
        else cause_.fetch_and(~bit,std::memory_order_relaxed);
    }
};
}
