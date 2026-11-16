// Original-free NWiiRecomp generated dispatcher startup-prefix test.
// V16_OWNER=1 uses code generated privately from owner-verified original DOL;
// V16_OWNER=0 uses independently authored synthetic PowerPC instructions.
#include "runtime/cpu_context.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

#ifndef V16_OWNER
#define V16_OWNER 0
#endif
constexpr uint32_t ENTRY=0x8000403Cu;
constexpr uint32_t REG_INIT=0x800041A8u;
constexpr uint32_t HARDWARE_BOUNDARY=0x800042E0u;
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t entry_calls=0, register_calls=0, boundary_calls=0;
static uint32_t syscalls=0, fallbacks=0;
void trace_call(uint32_t pc,CPUContext&) {
    switch (pc) {
    case ENTRY: ++entry_calls; break;
    case REG_INIT: ++register_calls; break;
    case HARDWARE_BOUNDARY: ++boundary_calls; break;
    default: throw std::runtime_error("unexpected function dispatch in startup prefix");
    }
}
bool handle_syscall(CPUContext& ctx) {
    if(ctx.pc!=HARDWARE_BOUNDARY)
        throw std::runtime_error("unexpected syscall outside test boundary");
    ++syscalls;
    ctx.is_running=false;
    return true;
}
void interpret_step(CPUContext&) {
    ++fallbacks;
    throw std::runtime_error("unexpected PowerPC interpreter fallback");
}
bool process_pending_callbacks(CPUContext&) {return false;}
void watch_hit(uint32_t,uint32_t,int) {}
void GX_WGPIPE_Write8(uint8_t) {}
void GX_WGPIPE_Write16(uint16_t) {}
void GX_WGPIPE_Write32(uint32_t) {}
void GX_WGPIPE_WriteF32(float) {}
void GX_WGPIPE_WriteF64(double) {}
uint16_t HW_Reg_Read16(uint32_t) {return 0;}
uint32_t HW_Reg_Read32(uint32_t) {return 0;}
void HW_Reg_Write16(uint32_t,uint16_t) {}
void HW_Reg_Write32(uint32_t,uint32_t) {}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
static uint64_t checks=0;
static void ck(bool condition,const char* message) {
    if(!condition)throw std::runtime_error(message);
    ++checks;
}
int main() {
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    constexpr uint32_t TRIALS=512;
    uint32_t rng=0x928ace32u;
    for(unsigned n=0;n<TRIALS;++n) {
        std::array<uint32_t,32> initial{};
        for(unsigned i=0;i<32;++i) {
            rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;
            initial[i]=rng;
            ctx->gpr[i]=initial[i];
        }
        ctx->pc=ENTRY;
        ctx->lr=0x81000000u+n*4u;
        ctx->is_running=true;
        auto before_inst=ctx->inst_count;
        run_game(*ctx);
        ck(!ctx->is_running,"did not stop at synthetic hardware boundary");
        ck(ctx->pc==ENTRY+8,"guest PC did not resume immediately after hardware boundary");
        ck(ctx->lr==ENTRY+8,"PPC BL did not update LR for hardware initializer");
#if V16_OWNER
        for(unsigned i=0;i<32;++i) {
            uint32_t expected=0;
            if(i==1)expected=0x80751CB8u;
            if(i==2)expected=0x80715EE0u;
            if(i==13)expected=0x8070E8E0u;
            ck(ctx->gpr[i]==expected,"real __init_registers GPR mismatch");
        }
        ck(ctx->inst_count-before_inst>=38,"too few original PPC instructions executed");
#else
        for(unsigned i=0;i<32;++i)
            ck(ctx->gpr[i]==(i==3?42u:initial[i]),"synthetic register initializer mismatch");
        ck(ctx->inst_count-before_inst>=5,"too few synthetic PPC instructions executed");
#endif
        ck(nwii::runtime::entry_calls==n+1,"start dispatched incorrectly");
        ck(nwii::runtime::register_calls==n+1,"register initializer dispatched incorrectly");
        ck(nwii::runtime::boundary_calls==n+1,"hardware boundary dispatched incorrectly");
        ck(nwii::runtime::syscalls==n+1,"test-only syscall count differs");
    }
    ck(nwii::runtime::fallbacks==0,"PowerPC fallback occurred");
    std::cout<<std::dec<<"PASS: "<<checks<<" NWiiRecomp-generated early startup assertions, "
             <<TRIALS<<" dispatched register-inits, "
             <<nwii::runtime::syscalls<<" synthetic boundary stops; interpreter=0; "
             <<"original_prefix="<<V16_OWNER<<"\n";
}
