// Source-only synthetic PowerPC callgraph executed using NWiiRecomp-generated C++.
#include "runtime/cpu_context.h"
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint64_t parent_trace=0, child_trace=0, incorrect_lr=0;
void trace_call(uint32_t pc,CPUContext& ctx){
    if(pc==0x80004000u)++parent_trace;
    else if(pc==0x80004018u){++child_trace;if(ctx.lr!=0x8000400cu)++incorrect_lr;}
    else throw std::runtime_error("unexpected trace pc");
}
void interpret_step(CPUContext&) {throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&) {return false;}
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
void func_80004000(nwii::runtime::CPUContext&);
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    constexpr uint32_t SP=0x80060000u, RETURN=0x80007000u;
    unsigned checks=0;
    auto test=[&](bool yes,const char* msg){if(!yes)throw std::runtime_error(msg);++checks;};
    for(uint32_t i=0;i<1024;++i){
        ctx->pc=0x80004000u;ctx->lr=RETURN;ctx->gpr[1]=SP;ctx->gpr[3]=i;
        ctx->mmu.write32(SP+8,0);
        func_80004000(*ctx);
        test(ctx->gpr[3]==i+1u,"translated callee arithmetic differs");
        test(ctx->pc==RETURN,"caller failed to return to guest LR");
        test(ctx->lr==RETURN,"caller failed to restore LR");
        test(ctx->gpr[1]==SP,"caller unexpectedly changed SP");
        test(ctx->mmu.read32(SP+8)==RETURN,"caller saved incorrect old LR");
    }
    test(nwii::runtime::parent_trace==1024,"wrong parent trace count");
    test(nwii::runtime::child_trace==1024,"wrong callee trace count");
    test(nwii::runtime::incorrect_lr==0,"BL assigned wrong return address");
    std::cout<<"PASS: "<<checks<<" synthetic NWiiRecomp guest callgraph assertions; 1024 linked BL calls\n";
}
