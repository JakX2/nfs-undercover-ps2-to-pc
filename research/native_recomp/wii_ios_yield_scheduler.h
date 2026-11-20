#pragma once
// Deterministic single-step IOS service scheduling for native Wii startup.
// A guest scheduling boundary authorizes exactly one Starlet service step.
// This is NOT emulation of ARM execution, wall-clock timing, or automatic IRQ dispatch.
#include "wii_ios_bus.h"
#include <cstdint>

namespace undercover::wii {
struct IosYieldState {
    StmIos::Pump progress;
    bool broadway_irq_level;
    bool guest_exception_ready;
    uint64_t serviced_steps;
};

class IosYieldScheduler {
public:
    explicit IosYieldScheduler(IosBus& bus) noexcept:bus_(bus){}
    IosYieldScheduler(const IosYieldScheduler&)=delete;
    IosYieldScheduler& operator=(const IosYieldScheduler&)=delete;

    IosYieldState service_one(uint32_t guest_msr) {
        // Hardware can already have an asserted, unhandled IRQ.
        // Never pump a second request or publish another completion until
        // the original guest explicitly handles the preceding interrupt.
        if(bus_.external_irq_level())
            return {StmIos::Pump::Busy,true,
                    bus_.external_exception_pending(guest_msr),steps_};
        const StmIos::Pump result=bus_.tick();
        ++steps_;
        return {result,bus_.external_irq_level(),
                bus_.external_exception_pending(guest_msr),steps_};
    }
    uint64_t serviced_steps() const noexcept{return steps_;}
private:
    IosBus& bus_;
    uint64_t steps_=0u;
};
}
