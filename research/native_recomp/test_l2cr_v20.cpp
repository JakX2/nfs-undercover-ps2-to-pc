// Independent test of modeled L2CR cache-control handshakes.
#include "runtime/cpu_context.h"
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
static int checks=0;
static void ck(bool x,const char* msg){if(!x)throw std::runtime_error(msg);++checks;}
int main(){
    auto ctx=std::make_unique<nwii::runtime::CPUContext>();
    for(uint32_t i=0;i<512;i++){
        ctx->l2cr=0;ctx->l2cr_busy_polls=0;
        const uint32_t preserve=(i<<4)&0x001fff00u;
        ctx->write_l2cr(preserve|0x00000001u);
        ck(ctx->read_l2cr()==preserve,"software must not set read-only L2IP");
        ctx->write_l2cr(preserve|0x00200000u);
        ck(ctx->read_l2cr()==(preserve|0x00200001u),"invalidate starts busy");
        ck(ctx->read_l2cr()==(preserve|0x00200001u),"second busy poll");
        ck(ctx->read_l2cr()==(preserve|0x00200000u),"busy becomes clear");
        ck(ctx->l2cr==preserve+0x00200000u,"L2I stays set until software clears");
        ctx->write_l2cr(ctx->read_l2cr()&~0x00200000u);
        ck(ctx->read_l2cr()==preserve,"clearing L2I retains other cache bits");
        ctx->write_l2cr(ctx->read_l2cr()|0x80000000u);
        ck(ctx->read_l2cr()==(preserve|0x80000000u),"L2E becomes visible");
    }
    std::cout<<"PASS: "<<checks<<" L2CR read-only status and bounded invalidate checks\n";
}
