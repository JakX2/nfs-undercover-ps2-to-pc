// Original-free contract tests. Link against owner-private NWiiRecomp-generated
// functions; this source contains no original game instructions or assets.
#include "loader/loader.h"
#include "runtime/cpu_context.h"
#include <array>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace nwii::runtime {
bool g_trace_calls=false;
uint32_t g_watch_addr=0;
void trace_call(uint32_t,CPUContext&) {}
void interpret_step(CPUContext&) {throw std::runtime_error("unexpected interpreter fallback");}
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
extern "C" void v13_guest_nibble(nwii::runtime::CPUContext&);
extern "C" void v13_guest_copy(nwii::runtime::CPUContext&);
static int checks=0;
static void check(bool ok,const char* what){if(!ok)throw std::runtime_error(what);++checks;}
static uint32_t hex32(const std::string& s){return static_cast<uint32_t>(std::stoul(s,nullptr,16));}
int main(int argc,char** argv) {
    if(argc !=4){std::cerr<<"Usage: test_real_leaf_v13 OWNER.DOL NIBBLE_ADDR_HEX COPY_ADDR_HEX\n";return 2;}
    const uint32_t nibble_pc=hex32(argv[2]),copy_pc=hex32(argv[3]);
    nwii::loader::Executable exe;
    check(exe.load_dol(argv[1]),"original owner DOL is loadable");
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    // Verify each selected guest PC maps to an original initialized text section.
    for(auto pc:{nibble_pc,copy_pc}){
        bool found=false;
        for(const auto& s:exe.sections)if(s.is_text && pc>=s.address &&
                 uint64_t(pc)+4<=uint64_t(s.address)+s.size){
            const size_t offset=pc-s.address;
            const uint32_t word=(uint32_t(s.data[offset])<<24)|
                    (uint32_t(s.data[offset+1])<<16)|(uint32_t(s.data[offset+2])<<8)|s.data[offset+3];
            ctx->mmu.write32(pc,word);
            check(ctx->mmu.read32(pc)==word,"original guest opcode roundtrip");
            found=true;
            break;
        }
        check(found,"guest function PC missing original text section");
    }
    const uint32_t LR=0x80001234u;
    const auto reference=[](uint32_t value)->uint32_t {
        // Semantic specification independent of emitted PPC instruction sequence.
        uint32_t c=value<=9?value+48u:(value&0xffu)+87u;
        return static_cast<uint32_t>(static_cast<int32_t>(static_cast<int8_t>(c)));
    };
    for(uint32_t v=0;v<256;v++){
        ctx->pc=nibble_pc;ctx->lr=LR;ctx->gpr[3]=v;
        v13_guest_nibble(*ctx);
        check(ctx->gpr[3]==reference(v),"original nibble function result differs");
        check(ctx->pc==LR,"original nibble function didn't return to LR");
    }
    for(uint32_t v:{0x00000101u,0x0000ffffu,0xffffffffu,0x8000000au,0x0000ff0au}){
        ctx->pc=nibble_pc;ctx->lr=LR;ctx->gpr[3]=v;
        v13_guest_nibble(*ctx);
        check(ctx->gpr[3]==reference(v),"original nibble high-value behavior differs");
        check(ctx->pc==LR,"nibble high-value didn't return to LR");
    }
    static constexpr uint32_t SRC=0x80002000u,DST=0x80003000u;
    // Exercise actual guest MMU byte loads/stores and loop backedges.
    std::vector<std::vector<uint8_t>> strings={ {}, {'N','F','S'},
        {0x7f,0x80,0xfe,0xff}, std::vector<uint8_t>(127,'X'),
        std::vector<uint8_t>(511,'R')};
    for(const auto& str:strings){
        for(size_t i=0;i<str.size();i++)ctx->mmu.write8(SRC+uint32_t(i),str[i]);
        ctx->mmu.write8(SRC+uint32_t(str.size()),0);
        for(size_t i=0;i<str.size()+2;i++)ctx->mmu.write8(DST+uint32_t(i),0xCE);
        ctx->pc=copy_pc;ctx->lr=LR;ctx->gpr[3]=DST;ctx->gpr[4]=SRC;
        v13_guest_copy(*ctx);
        check(ctx->pc==LR,"original copy function didn't return to LR");
        check(ctx->gpr[3]==DST+str.size(),"copy destination end register incorrect");
        check(ctx->gpr[4]==SRC+str.size(),"copy source end register incorrect");
        for(size_t i=0;i<str.size();i++)
            check(ctx->mmu.read8(DST+uint32_t(i))==str[i],"copied byte differs");
        check(ctx->mmu.read8(DST+uint32_t(str.size()))==0,"copy did not zero-terminate");
        check(ctx->mmu.read8(DST+uint32_t(str.size()+1))==0xCE,"copy wrote beyond terminator");
    }
    std::cout<<"PASS: "<<checks<<" original-game translated leaf-function assertions; "
             <<"261 nibble inputs and 5 guest-MMU string cases; no interpreter fallback\n";
}
