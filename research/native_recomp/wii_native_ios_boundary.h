#pragma once
#include "wii_native_ios_transport.h"
#include "native_external_irq.h"
#include <array>
#include <cstddef>

namespace undercover::wii {
// A small CPU-thread bridge for an independently certified resume boundary.
// It does not execute guest instructions or call the legacy HLE dispatcher.
// The caller MUST redispatch when NativeEntered is returned, and must not
// use the legacy IOS interrupt path when NativeMasked is returned.
enum class NativeBoundaryRoute { Unsafe, Idle, Serviced, OtherPending, NativeMasked, NativeEntered };
struct NativeBoundaryResult {
    NativeBoundaryRoute route;
    std::optional<IosYieldState> service;
    uint32_t enabled_pi;
};
namespace detail {
struct NativeHollywoodGate {
    uint32_t enabled_pi;
    bool external_exception_pending(uint32_t msr) const noexcept{
        return (msr&IosBus::MSR_EE)!=0u&&(enabled_pi&HollywoodIrq::PI_HOLLYWOOD)!=0u;
    }
};
}
template<class Cpu,std::size_t N>
NativeBoundaryResult service_native_ios_boundary(NativeIosTransport& transport,Cpu& cpu,
                          const std::array<uint8_t,N>& original_vector,bool safe_boundary){
    static_assert(N>=4&&N<=0x100&&N%4==0);
    using R=NativeBoundaryRoute;
    // Do not pump Starlet in a host callback, in-flight context dispatch,
    // pending HLE reschedule, stopped CPU or uncertified AOT body.
    // The caller must additionally account for guest-side nested handlers.
    if(!safe_boundary||!cpu.is_running||cpu.in_callback||cpu.dispatch_saved_ctx||
       cpu.ext_resched_pending||!cpu.pc||(cpu.pc&3u)||
       (cpu.msr&ExternalUnsupportedMsr)||!cpu.mmu.get_ptr(cpu.pc)||!cpu.mmu.get_ptr(cpu.pc+3u))
        return {R::Unsafe,std::nullopt,0u};
    uint32_t active=transport.active_pi_causes();
    std::optional<IosYieldState> service;
    // Existing enabled non-Hollywood causes belong to the other runtime
    // devices. Don't consume an IOS step before those interrupts are handled.
    if(!active){
        service=transport.service_at_guest_boundary(cpu.msr);
        active=transport.active_pi_causes();
    }
    constexpr uint32_t hollywood=HollywoodIrq::PI_HOLLYWOOD;
    if((active&hollywood)==0u)
        return {active?R::OtherPending:(service?R::Serviced:R::Idle),service,active};
    if((cpu.msr&IosBus::MSR_EE)==0u)return {R::NativeMasked,service,active};
    // Only installed original vector bytes authorize the CPU mutation.
    // Leave the actual latched mailbox/PI state intact, including other causes.
    if(!cpu.mmu.get_ptr(ExternalVector)||!cpu.mmu.get_ptr(ExternalVector+uint32_t(N)-1u))
        throw std::runtime_error("native IOS exception vector not mapped");
    const detail::NativeHollywoodGate gate{active};
    if(enter_external_irq(cpu,gate,original_vector,true)!=ExternalEntry::Entered)
        throw std::runtime_error("native IOS exception entry unexpectedly deferred");
    return {R::NativeEntered,service,active};
}
}
