#include "wii_formatter_caller_integer.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t d(unsigned op,unsigned r,unsigned a,unsigned n){return (op<<26)|(r<<21)|(a<<16)|(n&0xffffu);}
constexpr uint32_t x(unsigned r,unsigned a,unsigned b,unsigned xo,bool rc=false){return (31u<<26)|(r<<21)|(a<<16)|(b<<11)|(xo<<1)|unsigned(rc);}
int main(){
    std::array<uint32_t,32> gp{};gp[3]=0x80000080u;gp[4]=0xffffffffu;
    const std::array<CallerIntegerInput,1> a{{{3,gp[3]}}};
    const std::array<CallerIntegerInput,2> ab{{{3,gp[3]},{4,gp[4]}}};
    const auto run=[&](uint32_t w,std::span<const CallerIntegerInput> i,uint32_t xer=0u){return predict_caller_integer(w,gp,0x12345678u,xer,i);};
    auto p=run(d(14,5,3,0xffff),a);assert(p&&p->reg==5&&p->value==0x8000007fu&&p->cr==0x12345678u);
    p=run(d(15,5,0,0xffff),{});assert(p&&p->value==0xffff0000u);
    p=run(d(28,3,5,0x80),a,0x80000000u);assert(p&&p->value==0x80u&&p->cr==0x52345678u);
    p=run(x(3,5,0,954,true),a);assert(p&&p->reg==5&&p->value==0xffffff80u&&p->cr==0x82345678u);
    p=run(x(3,5,0,922),a);assert(p&&p->value==0x80u);
    p=run(x(5,3,4,266),ab);assert(p&&p->value==0x8000007fu);
    p=run(x(5,3,4,40),ab);assert(p&&p->value==0x7fffff7fu);
    p=run(x(3,5,3,444),a);assert(p&&p->value==gp[3]);
    p=run(x(3,5,4,316),ab);assert(p&&p->value==0x7fffff7fu);
    p=run(d(11,0,3,0),a,0x80000000u);assert(p&&!p->reg&&p->cr==0x92345678u);
    p=run(d(10,4,3,0),a);assert(p&&!p->reg&&p->cr==0x14345678u);
    p=run(x(0,3,4,32),ab);assert(p&&!p->reg&&p->cr==0x82345678u);
    const auto rot=(21u<<26)|(3u<<21)|(5u<<16)|(1u<<11)|(31u<<6)|(0u<<1);
    p=run(rot,a);assert(p&&p->value==1u);
    assert(!run(d(14,5,3,1),{}));
    assert(!run(d(14,5,3,1),ab));
    assert(!run(d(14,14,3,1),a));
    assert(!run(d(14,1,3,1),a));
    assert(!run(d(14,2,3,1),a));
    assert(!run(d(14,13,3,1),a));
    assert(!run(d(34,5,3,0),a));
    assert(!run(d(13,5,3,1),a));
    assert(!run(x(5,3,4,778),ab)); // OE add
    assert(!run(x(3,5,1,954),a)); // reserved RB
    assert(!run(d(11,1,3,0),a)); // L=1
    assert(!run(x(0,3,4,32,true),ab));
    const std::array<CallerIntegerInput,1> wrong{{{3,0u}}};
    const std::array<CallerIntegerInput,2> dup{{{3,gp[3]},{3,gp[3]}}};
    const std::array<CallerIntegerInput,1> bad{{{32,0u}}};
    assert(!run(d(14,5,3,1),wrong));assert(!run(d(14,5,3,1),dup));assert(!run(d(14,5,3,1),bad));
    // All byte values, including the sign boundary, verify against an
    // independent arithmetic expression rather than the implementation.
    for(unsigned i=0;i<256;++i){
        gp[3]=i;const std::array<CallerIntegerInput,1> one{{{3,i}}};
        p=run(x(3,5,0,954),one);
        assert(p&&p->value==(i<128u?i:0xffffff00u+i));
    }
    std::cout<<"FORMATTER_CALLER_INTEGER_TEST byte_patterns=256 original_execution=0\n";
}
