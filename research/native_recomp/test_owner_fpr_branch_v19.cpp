// Source-only branch oracle for original, privately recompiled __OSFPRInit.
// The test is executed against an owner-only temporary translated DOL slice.
#include "runtime/cpu_context.h"
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
namespace nwii::runtime {
bool g_trace_calls=false;
uint32_t g_watch_addr=0;
void trace_call(uint32_t,CPUContext&) {}
void interpret_step(CPUContext&){throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&){return false;}
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
static uint32_t stops=0;
bool handle_syscall(CPUContext& ctx){
    if(ctx.pc!=0x80004044u)throw std::runtime_error("unexpected syscall");
    ++stops;ctx.is_running=false;return true;
}
}
extern "C" void run_game(nwii::runtime::CPUContext&);
static unsigned checks=0;
static void ck(bool yes,const char* msg){if(!yes)throw std::runtime_error(msg);++checks;}
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    uint32_t seed=0x573ecc24u;
    const auto rand32=[&](){seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;return seed;};
    for(uint32_t n=0;n<256;++n){
        const bool pse=(n&1u)!=0;
        ctx->gpr[13]=0x8070e8e0u;
        ctx->pc=0x8051fbb0u;
        ctx->lr=0x80004044u;
        ctx->msr=0;
        ctx->hid2=pse?0x20000000u:0u;
        ctx->is_running=true;
        ctx->fpscr=~rand32();
        ctx->gqr.fill(0);
        const float ps0=4.25f,ps1=-3.5f;
        ctx->mmu.write_f32(0x8070db08u,ps0);
        ctx->mmu.write_f32(0x8070db0cu,ps1);
        const uint32_t low=rand32();
        const uint64_t bits=0x3ff0000000000000ull|low;
        ctx->mmu.write64(0x8070db10u,bits);
        double scalar=0;
        std::memcpy(&scalar,&bits,8);
        for(unsigned k=0;k<32;++k){
            ctx->fpr[k]=100+k;
            ctx->ps1[k]=200+k;
        }
        run_game(*ctx);
        ck(ctx->pc==0x80004044u,"FPR service failed to return");
        ck(!ctx->is_running,"termination boundary not reached");
        ck(ctx->lr==0x80004044u,"FPR service damaged guest LR");
        ck(ctx->msr==0x2000u,"FP-enable MSR not set");
        ck(ctx->fpscr==low,"FPSCR write mismatched");
        for(unsigned k=0;k<32;++k){
            ck(ctx->fpr[k]==scalar,"scalar bank missing initialization");
            ck(ctx->ps1[k]==(pse?double(ps1):double(200+k)),"paired-single HID2 branch wrong");
        }
    }
    ck(nwii::runtime::stops==256,"wrong stop count");
    std::cout<<"PASS: "<<checks<<" original Wii FPR HID2 branch and FPSCR assertions\n";
}
