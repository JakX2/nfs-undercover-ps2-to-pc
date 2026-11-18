#pragma once
// Bounded boot-time synchronous SC entry helper, not a general Wii exception
// scheduler. Reject unknown vectors or modified RAM before native execution.
#include <array>
#include <cstdint>
#include <stdexcept>
template<class Context,class Handler,size_t N>
void boot_native_sc(Context& c,uint32_t vector,const std::array<uint8_t,N>& expected,Handler execute){
    if((c.msr&0x8000u)||c.dispatch_saved_ctx)
        throw std::runtime_error("native SC entry requires interrupts disabled and no active dispatch context");
    for(size_t i=0;i<N;++i)
        if(c.mmu.read8(vector+uint32_t(i))!=expected[i])
            throw std::runtime_error("native SC vector RAM does not match authenticated translated bytes");
    const uint32_t prior_msr=c.msr;
    const uint32_t resume=c.pc+4u;
    c.srr0=resume;c.srr1=prior_msr;
    // SC hardware entry clears exception-mode control bits. This bridge is
    // only used during the verified no-EE boot path.
    c.msr=prior_msr&~0x0000ef33u;c.pc=vector;
    execute(c);
    if(c.pc!=resume||c.msr!=prior_msr||c.srr0!=resume||c.dispatch_saved_ctx)
        throw std::runtime_error("native SC vector did not restore exact bounded exception state");
}
