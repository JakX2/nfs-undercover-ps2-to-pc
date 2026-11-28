// Original-free Wii PPC external-IRQ reentry contract.
// A restored MSR without RI enters the SDK's default-exception path,
// not the installed interrupt dispatch table. No owner instructions used.
#include "wii_pending_external_reentry_v932.h"
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>

namespace {
struct Ram {
    std::array<uint8_t,4> vector{0x60u,0x00u,0x00u,0x00u}; // synthetic nop
    uint8_t* get_ptr(uint32_t a) {
        return a>=undercover::wii::ExternalVector &&
               a<undercover::wii::ExternalVector+vector.size()
            ? &vector[a-undercover::wii::ExternalVector] : nullptr;
    }
    uint8_t read8(uint32_t a) {
        auto* p=get_ptr(a);
        assert(p);
        return *p;
    }
};
struct Cpu {
    struct Cr {bool lt=false,gt=false,eq=false,so=false;};
    std::array<uint32_t,32> gpr{};
    std::array<uint32_t,8> gqr{};
    std::array<Cr,8> cr{};
    uint32_t pc=0x80004000u,msr=0x8002u,srr0=0u,srr1=0u;
    uint32_t lr=0u,ctr=0u,xer=0u;
    uint64_t inst_count=64u;
    bool is_running=true,in_callback=false,dispatch_saved_ctx=false;
    Ram mmu;
};
using undercover::wii::PendingExternalReentry;

void accepts_recoverable_si() {
    Cpu cpu;
    PendingExternalReentry reentry;
    const auto vector=cpu.mmu.vector;
    assert(reentry.enter(cpu,8u,8u,vector,true,true));
    assert(reentry.stage()==1u && reentry.captured().stage()==1u);
    assert(cpu.pc==undercover::wii::ExternalVector);
    assert(cpu.srr0==0x80004000u && cpu.srr1==(0x8002u&undercover::wii::ExternalSrr1Mask));
    assert(cpu.msr==(0x8002u&~undercover::wii::ExternalMsrClear));
    assert(reentry.outer_poll(cpu,8u,8u,true));
    ++cpu.inst_count; // authentic outer dispatcher tick; no guest instruction
    assert(reentry.vector_entry(cpu,undercover::wii::ExternalVector,8u,8u,true));
    assert(reentry.stage()==3u);
}
void rejects_unrecoverable_or_masked() {
    for(const uint32_t msr : {0x8000u,0x8001u,0x0002u,0x0000u}) {
        Cpu cpu;
        cpu.msr=msr;
        PendingExternalReentry reentry;
        const auto vector=cpu.mmu.vector;
        assert(!reentry.enter(cpu,8u,8u,vector,true,true));
        assert(reentry.stage()==0u && reentry.failure()==1u);
        assert(cpu.pc==0x80004000u && cpu.msr==msr);
        assert(cpu.srr0==0u && cpu.srr1==0u);
    }
}
void rejects_modified_vector_and_source() {
    {
        Cpu cpu;
        PendingExternalReentry reentry;
        auto vector=cpu.mmu.vector;
        vector[0]^=1u;
        assert(!reentry.enter(cpu,8u,8u,vector,true,true));
        assert(reentry.failure()==1u && cpu.pc==0x80004000u);
    }
    {
        Cpu cpu;
        PendingExternalReentry reentry;
        assert(!reentry.enter(cpu,8u,0u,cpu.mmu.vector,true,true));
        assert(reentry.failure()==1u && cpu.pc==0x80004000u);
    }
}
}
int main() {
    accepts_recoverable_si();
    rejects_unrecoverable_or_masked();
    rejects_modified_vector_and_source();
    std::cout << "PASS: original-free recoverable pending-SI interrupt reentry\n";
}
