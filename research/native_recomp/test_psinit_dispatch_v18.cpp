// Original-free behavioral oracle for owner-local translated Undercover Wii
// __OSPSInit + PPCMfhid2 / PPCMthid2 / ICFlashInvalidate.
// Links NWiiRecomp-generated run_game. Original-game function bodies are private.
#include "runtime/cpu_context.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>

#ifndef V18_OWNER
#define V18_OWNER 0
#endif
namespace {
constexpr uint32_t ENTRY=0x8000403cu, REGS=0x800041a8u, HW=0x800042e0u;
constexpr uint32_t PS=0x80520fb4u, HIDR=0x804b79dcu, HIDW=0x804b79e4u;
constexpr uint32_t IC=0x805223acu, FPR=0x8051fbb0u, CACHE=0x80522540u;
constexpr uint32_t EXIT=ENTRY+8;
constexpr std::array<uint32_t,9> CALLS{ENTRY,REGS,HW,PS,HIDR,HIDW,IC,FPR,CACHE};
constexpr std::array<uint32_t,6> ORDER{PS,HIDR,HIDW,IC,FPR,CACHE};
uint64_t checks=0;
void ck(bool ok,const char* msg){if(!ok)throw std::runtime_error(msg);++checks;}
uint32_t rng(uint32_t& x){x^=x<<13;x^=x>>17;x^=x<<5;return x;}
}
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static std::array<uint32_t,CALLS.size()> traces{};
static std::array<uint32_t,ORDER.size()> order{};
static unsigned order_n=0;
static uint32_t original_hid0=0,original_hid2=0,original_msr=0;
static uint32_t base_stack=0;
static uint32_t syscalls=0,stops=0,callbacks=0,fallbacks=0;
void trace_call(uint32_t pc,CPUContext& ctx){
    for(size_t j=0;j<CALLS.size();++j){if(CALLS[j]==pc){++traces[j];goto found;}}
    throw std::runtime_error("unexpected entry into unselected Wii function");
found:
    if(pc==PS){
        ck(ctx.hid2==original_hid2,"HID2 changed before original PSInit");
        ck(ctx.hid0==original_hid0,"HID0 changed before original PSInit");
        ck(ctx.lr==0x800042f4u,"hardware BL -> PSInit wrong LR");
        base_stack=ctx.gpr[1];
    }
    if(pc==HIDR){
        ck(ctx.hid2==original_hid2,"HID2 pre-read state mismatch");
        ck(ctx.lr==0x80520fc4u,"PPCMfhid2 BL wrong return address");
    }
    if(pc==HIDW){
        ck(ctx.gpr[3]==(original_hid2|0xa0000000u),"original PSInit HID2 ORIS argument wrong");
        ck(ctx.lr==0x80520fccu,"PPCMthid2 BL wrong return address");
    }
    if(pc==IC){
        ck(ctx.hid2==(original_hid2|0xa0000000u),"HID2 write not visible to cache helper");
        ck(ctx.hid0==original_hid0,"HID0 changed before original IC helper");
        ck(ctx.lr==0x80520fd0u,"ICFlashInvalidate BL wrong return address");
    }
    if(pc==FPR){
        ck(ctx.gpr[1]==base_stack,"PSInit failed to restore caller stack pointer");
        ck(ctx.hid2==(original_hid2|0xa0000000u),"PSInit failed to set HID2 PSE/LSQE bits");
        ck(ctx.hid0==(original_hid0|0x00000800u),"ICFlashInvalidate failed to set HID0 ICFI");
        ck(ctx.gpr[3]==0u,"PSInit failed to clear r3 before GQR setup");
        for(uint32_t gqr:ctx.gqr) ck(gqr==0,"PSInit did not clear GQR0..7");
        ck(ctx.msr==(original_msr|0x2000u),"MSR FP-enable changed in PSInit");
    }
}
bool handle_syscall(CPUContext& ctx){
    ++syscalls;
    if(ctx.pc==EXIT){++stops;ctx.is_running=false;return true;}
    if(ctx.pc!=FPR&&ctx.pc!=CACHE)throw std::runtime_error("unexpected test-only syscall boundary");
    ck(ctx.lr==(ctx.pc==FPR?0x800042f8u:0x800042fcu),"hardware service caller LR changed");
    ck(ctx.hid2==(original_hid2|0xa0000000u),"HID2 changed after PSInit");
    ck(ctx.hid0==(original_hid0|0x00000800u),"HID0 changed after PSInit");
    order[order_n++]=ctx.pc;
    return true;  // explicitly NOT original Wii FPR or cache emulation
}
void interpret_step(CPUContext&){++fallbacks;throw std::runtime_error("PowerPC interpreter fallback");}
bool process_pending_callbacks(CPUContext&){++callbacks;return false;}
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
    uint32_t seed=0x8123ab94u;
    constexpr uint32_t N=512;
    for(uint32_t n=0;n<N;++n){
        auto& state=*ctx;
        for(uint32_t& r:state.gpr)r=rng(seed);
        state.msr=rng(seed)&~0x2000u;
        nwii::runtime::original_msr=state.msr;
        state.hid0=(n&1u)?(rng(seed)|0x00000800u):(rng(seed)&~0x00000800u);
        state.hid2=(n&1u)?(rng(seed)|0xa0000000u):(rng(seed)&~0xa0000000u);
        nwii::runtime::original_hid0=state.hid0;
        nwii::runtime::original_hid2=state.hid2;
        for(auto& gqr:state.gqr)gqr=rng(seed)|1u;
        state.lr=0x81340000u+n*4u;
        state.pc=ENTRY;
        state.is_running=true;
        nwii::runtime::order_n=0;
        nwii::runtime::order.fill(0);
        const uint32_t before_calls=nwii::runtime::syscalls;
        const auto before_instructions=state.inst_count;
        run_game(state);
        ck(!state.is_running,"missing test-only termination");
        ck(state.pc==EXIT&&state.lr==EXIT,"actual hardware init failed to return to original startup boundary");
        ck(state.msr==(nwii::runtime::original_msr|0x2000u),"FP-enable MSR bit mismatch");
        ck(state.hid2==(nwii::runtime::original_hid2|0xa0000000u),"final HID2 register mismatch");
        ck(state.hid0==(nwii::runtime::original_hid0|0x00000800u),"final HID0 register mismatch");
        for(auto gqr:state.gqr)ck(gqr==0,"final paired-single GQR differs");
        ck(state.gpr[1]==nwii::runtime::base_stack,"Wii PSInit did not restore r1");
        ck(state.mmu.read32(state.gpr[1]+4)==0x800042f4u,"PSInit did not save original LR into its stack frame");
        ck(state.inst_count-before_instructions>=40,"real instruction execution count too low");
        ck(nwii::runtime::syscalls-before_calls==3,"expected exactly FPR/cache/stop synthetic syscalls");
        ck(nwii::runtime::order_n==2 && nwii::runtime::order[0]==FPR && nwii::runtime::order[1]==CACHE,
           "remaining synthetic Wii service order differs");
#if V18_OWNER
        ck(state.gpr[1]==0x80751cb8u,"owner original __init_registers stack incorrect");
        ck(state.gpr[2]==0x80715ee0u,"owner original r2 initialization changed");
        ck(state.gpr[13]==0x8070e8e0u,"owner original r13 initialization changed");
#else
        ck(state.gpr[1]==0x80060000u,"synthetic register initializer stack changed");
#endif
        for(uint32_t entry_count:nwii::runtime::traces)ck(entry_count==n+1,"missing generated native function call");
        ck(nwii::runtime::stops==n+1,"wrong test-only stop count");
    }
    ck(nwii::runtime::fallbacks==0,"unexpected interpreter fallback count");
    ck(ctx->pending_cb_count.load()==0,"unexpected queued hardware callback");
    ck(nwii::runtime::syscalls==3*N,"unexpected total synthetic syscall count");
    std::cout<<std::dec<<"PASS: "<<checks<<" V18 real NWiiRecomp OSPSInit native assertions; starts="<<N
             <<" original="<<V18_OWNER<<" native guest calls="<<N*9
             <<" synthetic remaining service boundaries="<<N*2<<"\n";
}
