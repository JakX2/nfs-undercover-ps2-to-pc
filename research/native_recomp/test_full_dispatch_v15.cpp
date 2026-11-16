// Source-only host test for NWiiRecomp's ACTUAL generated run_game dispatcher.
// V15_REAL=1: original-game instructions are compiled only in owner-local files.
#include "runtime/cpu_context.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>

#ifndef V15_REAL
#define V15_REAL 0
#endif
constexpr uint32_t STOP=0x80004200u;
#if V15_REAL
constexpr uint32_t ENTRY=0x8007ADC8u, CALLEE=0x8007ADACu;
#else
constexpr uint32_t ENTRY=0x80004000u, CALLEE=0x80004018u;
#endif
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint64_t parents=0,callees=0,syscalls=0,interpreted=0,unrecognized=0;
static bool stop_only = false;
void trace_call(uint32_t pc, CPUContext&) {
    if(pc==ENTRY)++parents;
    else if(pc==CALLEE)++callees;
    else if(pc==STOP){} // test-only stop endpoint
    else ++unrecognized;
}
bool handle_syscall(CPUContext& ctx) {
    if(ctx.pc!=STOP)throw std::runtime_error("unexpected guest syscall");
    ++syscalls;
    ctx.is_running=false;
    stop_only=true;
    return true;
}
void interpret_step(CPUContext&) {
    ++interpreted;
    throw std::runtime_error("interpreter fallback must never be reached");
}
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
} // namespace nwii::runtime
extern "C" void run_game(nwii::runtime::CPUContext&);
static uint64_t checks=0;
static void ck(bool b,const char* msg){if(!b)throw std::runtime_error(msg);++checks;}
#if V15_REAL
static uint8_t hex(uint8_t nibble){return uint8_t(nibble<10?'0'+nibble:'a'+nibble-10);}
#endif
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    constexpr uint32_t STACK=0x80050000u;
    std::ostringstream output;
    auto* old_output=std::cout.rdbuf(output.rdbuf());
    try {
#if V15_REAL
    constexpr uint32_t SRC=0x80030000u,DST=0x80040000u;
    std::vector<size_t> lengths={0,1,2,3,4,7,15,16,31,64,127,256,511,1024};
    for(unsigned i=0;i<256;++i)lengths.push_back(1);
    uint32_t rng=0x13572468u;
    for(size_t run=0;run<lengths.size();++run){
        const auto len=lengths[run];
        std::vector<uint8_t> bytes(len);
        for(size_t i=0;i<len;++i){
            rng ^= rng<<13;rng ^= rng>>17;rng ^= rng<<5;
            bytes[i]=run>=14?uint8_t(run-14):uint8_t(rng);
            ctx->mmu.write8(SRC+uint32_t(i),bytes[i]);
        }
        for(size_t i=0;i<len*2+2;++i)ctx->mmu.write8(DST+uint32_t(i),0xCD);
        ctx->pc=ENTRY;ctx->lr=STOP;ctx->gpr[1]=STACK;
        ctx->gpr[3]=SRC;ctx->gpr[4]=uint32_t(len);ctx->gpr[5]=DST;
        std::array<uint32_t,5> saved{};
        for(unsigned i=0;i<5;++i){
            saved[i]=0xA0B0C0D0u+uint32_t(run)+uint32_t(i*0x10203u);
            ctx->gpr[27+i]=saved[i];
        }
        ctx->is_running=true;
        nwii::runtime::stop_only=false;
        const uint64_t before_calls=nwii::runtime::callees;
        const uint64_t before_syscalls=nwii::runtime::syscalls;
        run_game(*ctx);
        ck(!ctx->is_running&&nwii::runtime::stop_only,"did not stop at synthetic syscall");
        ck(nwii::runtime::syscalls==before_syscalls+1,"missing or duplicate stop syscall");
        ck(nwii::runtime::callees-before_calls==2*len,"translated native guest BL calls differ");
        ck(ctx->lr==STOP,"guest LR not restored");
        ck(ctx->pc==STOP,"test stop PC not restored");
        ck(ctx->gpr[1]==STACK,"guest SP changed");
        for(unsigned i=0;i<5;++i)ck(ctx->gpr[27+i]==saved[i],"nonvolatile register clobbered");
        for(size_t i=0;i<len;++i){
            ck(ctx->mmu.read8(DST+uint32_t(2*i))==hex(bytes[i]>>4),"high nibble mismatch");
            ck(ctx->mmu.read8(DST+uint32_t(2*i+1))==hex(bytes[i]&15),"low nibble mismatch");
        }
        ck(ctx->mmu.read8(DST+uint32_t(2*len))==0,"missing NUL");
        ck(ctx->mmu.read8(DST+uint32_t(2*len+1))==0xCD,"output overflow");
    }
    ck(nwii::runtime::parents==lengths.size(),"incorrect parent trace count");
    ck(nwii::runtime::syscalls==lengths.size(),"incorrect native SC stop count");
    ck(nwii::runtime::callees==4634,"incorrect total real Undercover calls");
#else
    for(uint32_t i=0;i<512;++i){
        ctx->pc=ENTRY;ctx->lr=STOP;ctx->gpr[1]=STACK;
        ctx->gpr[3]=i;ctx->is_running=true;
        ctx->mmu.write32(STACK+8,0);
        nwii::runtime::stop_only=false;
        run_game(*ctx);
        ck(!ctx->is_running&&nwii::runtime::stop_only,"missing synthetic stop");
        ck(ctx->gpr[3]==i+1,"native PPC arithmetic incorrect");
        ck(ctx->pc==STOP,"guest return PC was not restored");
        ck(ctx->lr==STOP,"guest LR was not restored");
        ck(ctx->gpr[1]==STACK,"guest SP mismatch");
        ck(ctx->mmu.read32(STACK+8)==STOP,"guest saved-LR stack mismatch");
    }
    ck(nwii::runtime::parents==512,"wrong synthetic parent trace count");
    ck(nwii::runtime::callees==512,"wrong synthetic callee trace count");
    ck(nwii::runtime::syscalls==512,"wrong synthetic stop count");
#endif
    ck(nwii::runtime::interpreted==0,"PowerPC interpreter invoked");
    ck(nwii::runtime::unrecognized==0,"unrecognized guest function PC");
    std::cout.rdbuf(old_output);
    std::cout<<std::dec<<"PASS: "<<checks<<" genuine NWiiRecomp run_game dispatcher assertions, "
             <<nwii::runtime::parents<<" parents, "<<nwii::runtime::callees
             <<" native guest calls, "<<nwii::runtime::syscalls<<" controlled stops; interpreter=0\n";
    return 0;
    } catch(...) {std::cout.rdbuf(old_output); throw;}
}
