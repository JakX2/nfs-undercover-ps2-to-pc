#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <stdexcept>

// Bounded PowerPC 750 external interrupt entry for the native dispatcher.
// Hardware contract: IBM 750CL manual, chapter 4; external exception vector
// offset 0x500. The low physical vector is represented by the runtime's
// cached MEM1 alias. No exception handler, context switch, rfi or timing is
// synthesized. Only a guest instruction boundary is a valid call site.
namespace undercover::wii {
enum class ExternalEntry { NotPending, Deferred, Entered };
inline constexpr uint32_t ExternalVector=0x80000500u;
inline constexpr uint32_t ExternalSrr1Mask=0x87c0ffffu;
inline constexpr uint32_t ExternalMsrClear=0x0004ef37u;
inline constexpr uint32_t ExternalUnsupportedMsr=0x00010041u; // ILE, IP, LE

template<class Context,class Bus,size_t N>
ExternalEntry enter_external_irq(Context& cpu,const Bus& bus,
                                 const std::array<uint8_t,N>& installed,
                                 bool safe_boundary){
    static_assert(N>=4&&N<=0x100&&N%4==0);
    if(!bus.external_exception_pending(cpu.msr))return ExternalEntry::NotPending;
    // Never overwrite an in-flight exception's SRRs, and never interrupt
    // within an unresumable host translation body.
    if(!safe_boundary||cpu.dispatch_saved_ctx)return ExternalEntry::Deferred;
    if(!cpu.pc||(cpu.pc&3u)||(cpu.msr&ExternalUnsupportedMsr))
        throw std::runtime_error("unsupported native external IRQ CPU mode or resume PC");
    for(size_t i=0;i<N;++i)
        if(cpu.mmu.read8(ExternalVector+uint32_t(i))!=installed[i])
            throw std::runtime_error("native external IRQ vector differs from authenticated installed bytes");
    const uint32_t prior=cpu.msr;
    // External interrupt resumes at the next not-yet-executed guest PC,
    // unlike synchronous SC which advances PC by four.
    cpu.srr0=cpu.pc;
    cpu.srr1=prior&ExternalSrr1Mask;
    cpu.msr=prior&~ExternalMsrClear;
    cpu.pc=ExternalVector;
    return ExternalEntry::Entered;
}
}
