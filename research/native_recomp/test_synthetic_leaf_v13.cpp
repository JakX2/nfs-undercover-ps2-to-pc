// Synthetic PowerPC functions generated via the same upstream emitter.
// Original game code is never needed by this portable regression.
#include "runtime/cpu_context.h"
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>

namespace nwii::runtime {
bool g_trace_calls=false;
uint32_t g_watch_addr=0;
void trace_call(uint32_t,CPUContext&) {}
void interpret_step(CPUContext&) {throw std::runtime_error("interpreter fallback in synthetic leaf");}
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
extern "C" void v13_guest_add(nwii::runtime::CPUContext&);
extern "C" void v13_guest_store(nwii::runtime::CPUContext&);
static int checks=0;
static void check(bool b,const char* msg){if(!b)throw std::runtime_error(msg);++checks;}
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    const uint32_t LR=0x80001020u;
    for(uint32_t i=0;i<256;++i){
        ctx->pc=0x80004000u;ctx->lr=LR;ctx->gpr[3]=i;
        v13_guest_add(*ctx);
        check(ctx->gpr[3]==i+1,"add1 PPC result mismatch");
        check(ctx->pc==LR,"add1 LR return mismatch");
    }
    for(unsigned i=0;i<256;++i){
        ctx->mmu.write8(0x80002200u,uint8_t(i));
        ctx->mmu.write8(0x80002300u,0);
        ctx->pc=0x80004008u;ctx->lr=LR;
        ctx->gpr[3]=0x80002300u;ctx->gpr[4]=0x80002200u;
        v13_guest_store(*ctx);
        check(ctx->mmu.read8(0x80002300u)==i,"guest MMU byte store mismatch");
        check(ctx->pc==LR,"store LR return mismatch");
    }
    std::cout<<"PASS: "<<checks<<" original-free NWiiRecomp-generated PPC execution assertions\n";
}
