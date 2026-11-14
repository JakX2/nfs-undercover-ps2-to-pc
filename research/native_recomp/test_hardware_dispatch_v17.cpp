// Test real generated run_game dispatch, with explicit test-only OS service
// boundaries. The owner mode's __init_hardware body is translated verbatim
// privately from the owner-verified Undercover Wii DOL. NEVER ship that body.
#include "runtime/cpu_context.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

#ifndef V17_OWNER
#define V17_OWNER 0
#endif
namespace {
constexpr uint32_t ENTRY=0x8000403cu, REGS=0x800041a8u, HW=0x800042e0u;
constexpr std::array<uint32_t,3> OS{0x80520fb4u,0x8051fbb0u,0x80522540u};
constexpr std::array<uint32_t,3> LR_SERVICE{0x800042f4u,0x800042f8u,0x800042fcu};
constexpr uint32_t EXIT=ENTRY+8;
uint64_t checks=0;
void ck(bool ok,const char* name){if(!ok)throw std::runtime_error(name);++checks;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint32_t start_hits=0,regs_hits=0,hardware_hits=0;
static uint32_t service_trace[3]={0,0,0};
static uint32_t syscalls=0,stops=0,fallbacks=0,callback_calls=0;
static std::array<uint32_t,3> order{};
static unsigned order_index=0;
static uint32_t msr_on_service=0;
void trace_call(uint32_t pc,CPUContext&) {
    if(pc==ENTRY) {++start_hits;return;}
    if(pc==REGS) {++regs_hits;return;}
    if(pc==HW) {++hardware_hits;return;}
    for(size_t i=0;i<OS.size();++i)if(pc==OS[i]){++service_trace[i];return;}
    throw std::runtime_error("unexpected traced guest function");
}
bool handle_syscall(CPUContext& ctx) {
    ++syscalls;
    if(ctx.pc==EXIT) {
        ++stops;
        if(order_index!=3)throw std::runtime_error("startup stopped before all hardware services");
        ctx.is_running=false;
        return true;
    }
    for(size_t i=0;i<OS.size();++i) {
        if(ctx.pc==OS[i]) {
            if(order_index!=i || ctx.lr!=LR_SERVICE[i])
                throw std::runtime_error("hardware service order/return-LR mismatch");
            if(!(ctx.msr&0x2000u))throw std::runtime_error("MSR bit not set before OS call");
            msr_on_service=ctx.msr;
            order[order_index++]=ctx.pc;
            // Test intentionally leaves the PPC guest CPU state unchanged.
            // This is NOT an implementation of Wii OS/HID/cache initialization.
            return true;
        }
    }
    throw std::runtime_error("unexpected native syscall outside explicit test boundary");
}
void interpret_step(CPUContext&){++fallbacks;throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){++callback_calls;return false;}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){}
void GX_WGPIPE_Write16(uint16_t){}
void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){}
void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){}
void HW_Reg_Write32(uint32_t,uint32_t){}
}
extern "C" void run_game(nwii::runtime::CPUContext& ctx);
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    uint32_t seed=0xbecafdedu;
    constexpr uint32_t N=512;
    for(uint32_t n=0;n<N;++n){
        for(unsigned i=0;i<32;++i){
            seed ^= seed<<13;seed ^= seed>>17;seed ^= seed<<5;
            ctx->gpr[i]=seed;
        }
        const uint32_t init_msr= (n&1u)?uint32_t((n*0x10000u)^0x1000u):uint32_t((n*0x10u)^0x8000u);
        ctx->msr=init_msr & ~0x2000u;
        const uint32_t expected_msr=ctx->msr |0x2000u;
        ctx->lr=0x81010000u+n*4u;
        ctx->pc=ENTRY;
        ctx->is_running=true;
        const auto before=ctx->inst_count;
        const auto pre_syscalls=nwii::runtime::syscalls;
        nwii::runtime::order_index=0;
        nwii::runtime::order.fill(0);
        run_game(*ctx);
        ck(!ctx->is_running,"no deterministic test-only stop");
        ck(ctx->pc==EXIT,"return PC differs from post-hardware startup boundary");
        ck(ctx->lr==EXIT,"hardware initializer failed to restore LR");
        ck(ctx->gpr[31]==EXIT,"hardware initializer failed to preserve link register in r31");
        ck(ctx->msr==expected_msr,"actual __init_hardware MSR/FP enable differs");
        ck(nwii::runtime::msr_on_service==expected_msr,"service saw wrong MSR");
        ck(ctx->inst_count-before>=18u,"too few translated instructions executed");
        ck(nwii::runtime::syscalls-pre_syscalls==4u,"wrong number of test-only system calls");
        ck(nwii::runtime::order_index==3u,"unexpected number of service requests");
        for(size_t i=0;i<OS.size();++i)ck(nwii::runtime::order[i]==OS[i],"wrong Wii service request order");
#if V17_OWNER
        for(unsigned i=0;i<32;++i){
            uint32_t expected=0;
            if(i==0)expected=expected_msr;
            if(i==1)expected=0x80751cb8u;
            if(i==2)expected=0x80715ee0u;
            if(i==13)expected=0x8070e8e0u;
            if(i==31)expected=EXIT;
            ck(ctx->gpr[i]==expected,"owner original register init or hardware MSR mismatch");
        }
#else
        ck(ctx->gpr[3]==42u,"synthetic register initializer r3 mismatch");
        ck(ctx->gpr[7]==expected_msr,"synthetic hardware MSR setup r7 mismatch");
#endif
        ck(nwii::runtime::start_hits==n+1u,"startup trace count mismatch");
        ck(nwii::runtime::regs_hits==n+1u,"register init trace count mismatch");
        ck(nwii::runtime::hardware_hits==n+1u,"hardware init trace count mismatch");
        for(size_t i=0;i<OS.size();++i)
            ck(nwii::runtime::service_trace[i]==n+1u,"service boundary dispatch count mismatch");
        ck(nwii::runtime::stops==n+1u,"synthetic post-hardware stop count mismatch");
    }
    ck(nwii::runtime::fallbacks==0,"PowerPC interpreter fallback invoked");
    ck(nwii::runtime::syscalls==4u*N,"total syscall boundary count mismatch");
    std::cout<<std::dec<<"PASS: "<<checks<<" hardware-entry native dispatcher assertions; runs="<<N
             <<" 3 service-boundary calls/run, no real Wii OS service emulation"
             <<"; original="<<V17_OWNER<<"\n";
}
