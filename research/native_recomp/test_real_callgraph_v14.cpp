// Original-free runtime test; links *privately generated* owner-DOL C++.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <array>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
namespace nwii::runtime {
bool g_trace_calls=true;
uint32_t g_watch_addr=0;
static uint64_t callee_calls=0,caller_calls=0, bad_lr=0;
void trace_call(uint32_t addr,CPUContext& ctx) {
    if(addr==0x8007ADACu) {
        ++callee_calls;
        if(ctx.lr!=0x8007ADFCu && ctx.lr!=0x8007AE08u)++bad_lr;
    } else if(addr==0x8007ADC8u) {
        ++caller_calls;
    } else throw std::runtime_error("unexpected traced PC");
}
void interpret_step(CPUContext&) {throw std::runtime_error("interpreter fallback");}
bool process_pending_callbacks(CPUContext&) {return false;}
void watch_hit(uint32_t,uint32_t,int) {}
void GX_WGPIPE_Write8(uint8_t) {}
void GX_WGPIPE_Write16(uint16_t) {}
void GX_WGPIPE_Write32(uint32_t) {}
void GX_WGPIPE_WriteF32(float) {}
void GX_WGPIPE_WriteF64(double) {}
uint16_t HW_Reg_Read16(uint32_t){return 0;}
uint32_t HW_Reg_Read32(uint32_t){return 0;}
void HW_Reg_Write16(uint32_t,uint16_t){}
void HW_Reg_Write32(uint32_t,uint32_t){}
} // namespace nwii::runtime
void func_8007ADC8(nwii::runtime::CPUContext&);
static uint64_t checks=0;
static void ck(bool value,const char* msg){if(!value)throw std::runtime_error(msg);++checks;}
static uint8_t digit(uint8_t nibble) {return uint8_t(nibble<10 ? '0'+nibble : 'a'+nibble-10);}
int main(int argc,char** argv) {
    if(argc!=2){std::cerr<<"Usage: test_real_callgraph_v14 OWNER.DOL\n";return 2;}
    nwii::loader::Executable exe;
    ck(exe.load_dol(argv[1]),"original DOL loading failed");
    const uint32_t PARENT=0x8007ADC8u,CHILD=0x8007ADACu;
    for(uint32_t pc:{PARENT,CHILD}){
        bool found=false;
        for(const auto& sec:exe.sections)
            if(sec.is_text && pc>=sec.address && uint64_t(pc)+4<=uint64_t(sec.address)+sec.size){
                found=true;
                break;
            }
        ck(found,"selected original function does not map to a DOL text section");
    }
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    constexpr uint32_t SRC=0x80030000u,DST=0x80040000u,STACK=0x80050000u,END=0x80009000u;
    std::vector<size_t> lengths={0,1,2,3,4,7,15,16,31,64,127,256,511,1024};
    for(unsigned v=0;v<256;++v)lengths.push_back(1);
    uint32_t seed=0x13572468u;
    uint64_t expected_calls=0;
    for(size_t run=0;run<lengths.size();++run){
        const size_t len=lengths[run];
        if(len > 2048)throw std::runtime_error("test length exceeds fixture buffer");
        std::vector<uint8_t> bytes(len);
        for(size_t i=0;i<len;++i){
            seed ^= seed <<13; seed ^= seed >>17; seed ^= seed << 5;
            bytes[i] = run>=14?uint8_t(run-14):uint8_t(seed);
            ctx->mmu.write8(SRC+uint32_t(i),bytes[i]);
        }
        for(size_t i=0;i<len*2+2;++i)ctx->mmu.write8(DST+uint32_t(i),0xCD);
        ctx->pc=PARENT;ctx->lr=END;
        ctx->gpr[1]=STACK;
        ctx->gpr[3]=SRC;ctx->gpr[4]=uint32_t(len);ctx->gpr[5]=DST;
        std::array<uint32_t,5> saved{};
        for(unsigned i=0;i<5;++i){
            saved[i]=0xA0B0C0D0u+uint32_t(i*0x10203)+uint32_t(run);
            ctx->gpr[27+i]=saved[i];
        }
        ctx->mmu.write32(STACK+8,0xDEADBEEFu);
        const uint64_t before_child=nwii::runtime::callee_calls;
        const uint64_t before_parent=nwii::runtime::caller_calls;
        func_8007ADC8(*ctx); // BL x2 per guest byte: genuine original-call graph
        ck(ctx->pc==END,"parent failed to restore LR and return to host sentinel");
        ck(ctx->lr==END,"parent failed to restore guest link register");
        ck(ctx->gpr[1]==STACK,"parent stack pointer not restored");
        for(unsigned i=0;i<5;++i)ck(ctx->gpr[27+i]==saved[i],"callee-saved guest register altered");
        ck(ctx->mmu.read32(STACK+4)==END,"caller did not save initial LR in the stack frame");
        ck(ctx->mmu.read32(STACK+8)==0xDEADBEEFu,"stack wrote beyond expected local frame");
        ck(nwii::runtime::callee_calls-before_child==2*len,"nibble helper call count differs");
        ck(nwii::runtime::caller_calls-before_parent==1,"parent entry count differs");
        for(size_t i=0;i<len;++i){
            ck(ctx->mmu.read8(DST+uint32_t(2*i))==digit(bytes[i]>>4),"high nibble differs");
            ck(ctx->mmu.read8(DST+uint32_t(2*i+1))==digit(bytes[i]&15u),"low nibble differs");
        }
        ck(ctx->mmu.read8(DST+uint32_t(2*len))==0,"output missing terminating NUL");
        ck(ctx->mmu.read8(DST+uint32_t(2*len+1))==0xCD,"output overran terminator");
        expected_calls+=2*len;
    }
    ck(nwii::runtime::bad_lr==0,"nested calls saw wrong link register");
    ck(nwii::runtime::callee_calls==expected_calls,"incorrect total direct guest calls");
    std::cout<<"PASS: "<<checks<<" actual Undercover two-function native callgraph assertions; "
             <<lengths.size()<<" input arrays, "<<expected_calls<<" nested BL edges, no interpreter fallback\n";
}
