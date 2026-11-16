// Original-free precision check of NWiiRuntime FPSCR selected-field model.
#include "runtime/cpu_context.h"
#include <cstdint>
#include <cstring>
#include <iostream>
#include <memory>
#include <stdexcept>
static unsigned checks=0;
static void ck(bool ok){if(!ok)throw std::runtime_error("FPSCR selected field mismatch");++checks;}
static uint32_t fm_mask(uint32_t fm){
    uint32_t mask=0;
    for(unsigned i=0;i<8;++i)if(fm&(0x80u>>i))mask|=(0xfu<<(28-4*i));
    return mask;
}
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    uint32_t seed=0x1294de36;
    for(unsigned n=0;n<1024;++n){
        seed^=seed<<13;seed^=seed>>17;seed^=seed<<5;
        const uint32_t low=seed;
        const uint64_t image=0x3ff0000000000000ull|low;
        std::memcpy(&ctx->fpr[7],&image,8);
        const uint32_t initial=~seed;
        for(uint32_t fm:{0u,1u,0x12u,0x80u,0xa5u,0xffu}){
            ctx->fpscr=initial;
            ctx->mtfsf(fm,7);
            const uint32_t expected=(initial&~fm_mask(fm))|(low&fm_mask(fm));
            ck(ctx->fpscr==expected);
        }
    }
    std::cout<<"PASS: "<<checks<<" synthetic FPSCR field-mask assertions\n";
}
