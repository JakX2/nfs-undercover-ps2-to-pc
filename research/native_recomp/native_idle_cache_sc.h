#pragma once
#include "native_sc_vector_v63.h"

// Bounded synchronous cache-maintenance SC after interrupts have been enabled.
// Caller must establish that no pending interrupt/callback can redirect rfi.
// Original installed vector bytes are authenticated before entering it.
// Unlike boot_native_sc, this lane accepts prior MSR.EE=1 and verifies it
// is restored. This is not an external interrupt or general scheduler.
template<class Context,class Handler,size_t N>
void native_idle_cache_sc(Context& c,uint32_t vector,
                          const std::array<uint8_t,N>& expected,
                          bool no_pending_interrupt,Handler execute){
    if(!no_pending_interrupt||c.dispatch_saved_ctx)
        throw std::runtime_error("native idle cache SC requires no pending interrupt or active dispatch");
    for(size_t i=0;i<N;++i)
        if(c.mmu.read8(vector+uint32_t(i))!=expected[i])
            throw std::runtime_error("native idle cache SC vector RAM does not match authenticated bytes");
    const uint32_t prior_msr=c.msr,resume=c.pc+4u;
    c.srr0=resume;c.srr1=prior_msr;
    c.msr=prior_msr&~0x0000ef33u;c.pc=vector;
    execute(c);
    if(c.pc!=resume||c.msr!=prior_msr||c.srr0!=resume||c.dispatch_saved_ctx)
        throw std::runtime_error("native idle cache SC did not restore exact exception state");
}
