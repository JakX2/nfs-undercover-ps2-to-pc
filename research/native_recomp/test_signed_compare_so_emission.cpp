// Original-free test of the patched signed-immediate compare expressions.
// The inputs are synthetic; this does not execute original game code.
#include <array>
#include <cstdint>
#include <cassert>
#include <iostream>

struct Flag {
    bool lt,gt,eq,so;
    bool operator==(const Flag&) const = default;
};
struct Context {
    std::array<uint32_t,32> gpr{};
    std::array<Flag,8> cr{};
    uint32_t xer=0;
};
int main(){
    constexpr std::array<uint32_t,8> values{
        0u,1u,0x7fffu,0x8000u,0x7fffffffu,0x80000000u,
        0xffff8000u,0xffffffffu};
    constexpr std::array<int,5> immediates{-32768,-1,0,1,32767};
    unsigned n=0;
    for(unsigned bf=0;bf<8;++bf)
    for(auto value:values)
    for(int imm:immediates)
    for(unsigned old_so=0;old_so<2;++old_so)
    for(unsigned so=0;so<2;++so){
        Context ctx;ctx.gpr[5]=value;ctx.xer=so?0x80000000u:0u;
        for(auto& f:ctx.cr) f={true,false,true,bool(old_so)};
        const auto old=ctx.cr;const auto gp=ctx.gpr;const auto xer=ctx.xer;
        // These are the corrected emitted expressions, not a guest step.
        ctx.cr[bf].lt = ((int32_t)ctx.gpr[5] < imm);
        ctx.cr[bf].gt = ((int32_t)ctx.gpr[5] > imm);
        ctx.cr[bf].eq = ((int32_t)ctx.gpr[5] == imm);
        ctx.cr[bf].so = ((ctx.xer >> 31u) & 1u) != 0u;
        // Independent, full-width signed reference avoids a signed cast.
        const int64_t signed_value =
            value<0x80000000u?int64_t(value):int64_t(value)-0x100000000ll;
        const Flag expected{signed_value<imm,signed_value>imm,
                            signed_value==imm,bool(so)};
        assert(ctx.cr[bf]==expected);
        for(unsigned j=0;j<8;++j)if(j!=bf)assert(ctx.cr[j]==old[j]);
        assert(ctx.gpr==gp&&ctx.xer==xer);
        ++n;
    }
    assert(n==1280u);
    std::cout<<"CMPWI_EMITTED_EXPRESSION_TEST cases="<<n
             <<" signed_boundaries=1 so_copy=1 untouched_cr=1"
             <<" gpr_xer_preserved=1 original_execution=0\n";
}
