// Owner-local Wii DOL image test using REAL NWiiRuntime Executable and CPUContext.
// No original executable or game-generated C++ is bundled or redistributed.
#include "runtime/cpu_context.h"
#include "loader/loader.h"
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace nwii::runtime {
// Hardware stubs used ONLY by this test executable, not a Wii emulator.
uint32_t g_watch_addr = 0;
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
} // namespace nwii::runtime

// The symbol and CPUContext reference type are exactly what the NWii
// recompiler emits; the IMPLEMENTATION below is a synthetic fixture,
// not a recompiled function from Undercover.
extern "C" void run_game(nwii::runtime::CPUContext& ctx);
static void test(bool good,const char* why) {
    if(!good)throw std::runtime_error(why);
}
int main(int argc,char** argv) {
    if(argc!=2){std::cerr<<"Usage: test_dol_cpu_image_v12 path/to/original.dol\n";return 2;}
    nwii::loader::Executable exe;
    test(exe.load_dol(argv[1]),"DOL loader rejected input");
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    size_t copied=0, bss_bytes=0, initialized_in_bss=0;
    for(const auto& sec:exe.sections) if(sec.is_bss) {
        auto* p=ctx->mmu.get_ptr(sec.address);
        test(p!=nullptr,"BSS outside CPUContext MMU");
        std::memset(p,0xaa,sec.size); // show BSS really gets cleared
        for(uint32_t i=0;i<sec.size;++i)ctx->mmu.write8(sec.address+i,0);
        bss_bytes+=sec.size;
    }
    for(const auto& sec:exe.sections)if(!sec.is_bss) {
        auto* p=ctx->mmu.get_ptr(sec.address);
        test(p!=nullptr,"text/data outside CPUContext MMU");
        for(uint32_t i=0;i<sec.size;++i)ctx->mmu.write8(sec.address+i,sec.data[i]);
        copied+=sec.size;
    }
    for(const auto& sec:exe.sections)if(!sec.is_bss) {
        auto* p=ctx->mmu.get_ptr(sec.address);
        test(std::memcmp(p,sec.data.data(),sec.size)==0,"guest text/data image differs from file");
    }
    for(const auto& bss:exe.sections)if(bss.is_bss) {
        std::vector<uint8_t> expected(bss.size,0);
        for(const auto& sec:exe.sections) if(!sec.is_bss) {
            const uint64_t lo=std::max<uint64_t>(bss.address,sec.address);
            const uint64_t hi=std::min<uint64_t>(uint64_t(bss.address)+bss.size,
                                                 uint64_t(sec.address)+sec.size);
            if(lo<hi) {
                initialized_in_bss+=hi-lo;
                std::memcpy(expected.data()+(lo-bss.address),sec.data.data()+(lo-sec.address),hi-lo);
            }
        }
        const auto* memory=ctx->mmu.get_ptr(bss.address);
        test(std::memcmp(memory,expected.data(),bss.size)==0,
             "BSS zero/data overlay sequence mismatch");
    }
    ctx->pc=exe.entry_point;
    test(ctx->mmu.get_ptr(ctx->pc)!=nullptr,"entry PC not mapped to host memory");
    uint8_t* entry=ctx->mmu.get_ptr(ctx->pc);
    const uint32_t word=(uint32_t(entry[0])<<24)|(uint32_t(entry[1])<<16)|
                         (uint32_t(entry[2])<<8)|entry[3];
    test(ctx->mmu.read32(ctx->pc)==word,"entry instruction endian readback mismatch");
    ctx->gpr[3]=0xfffffff0u;
    ctx->gpr[4]=0x30u;
    ctx->lr=0x81234568u;
    run_game(*ctx); // synthetic linked translation boundary, not Undercover execution
    test(ctx->gpr[3]==0x20u,"synthetic guest register arithmetic failed");
    test(ctx->pc==ctx->lr,"synthetic LR return failed");
    test(ctx->mmu.read32(0x80001000u)==0x20u,"synthetic guest memory write failed");
    test(!ctx->is_running,"synthetic stop flag failed");
    std::cout<<"PASS: real NWiiRuntime DOL loader + MMU image + synthetic linked dispatch\n"
             <<" original_entry=0x"<<std::hex<<exe.entry_point
             <<" synthetic_return=0x"<<ctx->lr
             <<" word=0x"<<word<<std::dec<<" loaded="<<copied
             <<" bss="<<bss_bytes<<" initialized_overlapping_bss="<<initialized_in_bss
             <<" sections="<<exe.sections.size()<<"\n";
}
