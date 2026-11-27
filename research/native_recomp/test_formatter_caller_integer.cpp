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
    p=predict_caller_integer(x(3,16,3,444),gp,0u,0u,a,1u<<16);
    assert(p&&p->reg==16u&&p->value==gp[3]);
    assert(!predict_caller_integer(x(3,14,3,444),gp,0u,0u,a,1u<<16));
    assert(!predict_caller_integer(x(3,2,3,444),gp,0u,0u,a,1u<<2));
    assert(!predict_caller_integer(x(3,16,3,444),gp,0u,0u,a,(1u<<16)|1u));
    // All byte values, including the sign boundary, verify against an
    // independent arithmetic expression rather than the implementation.
    for(unsigned i=0;i<256;++i){
        gp[3]=i;const std::array<CallerIntegerInput,1> one{{{3,i}}};
        p=run(x(3,5,0,954),one);
        assert(p&&p->value==(i<128u?i:0xffffff00u+i));
    }
    // Runtime stack base is deliberately varied: no fixed address is a
    // valid substitute for the private symbolic parent stack identity.
    for(const auto sp:{0x80000000u,0x80012000u,0x817ffd40u}){
        gp[1]=sp;gp[7]=sp;gp[8]=sp+8u;
        auto move=predict_caller_stack_move(x(1,5,1,444),gp,0x12345678u,sp);
        assert(move&&move->reg==5u&&move->value==sp&&move->cr==0x12345678u);
        move=predict_caller_stack_move(x(7,6,7,444),gp,0x87654321u,sp);
        assert(move&&move->reg==6u&&move->value==sp&&move->cr==0x87654321u);
        assert(!predict_caller_stack_move(x(1,5,1,444,true),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,5,7,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(8,5,8,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,16,1,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,1,1,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,2,1,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,13,1,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(7,7,7,444),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,5,1,28),gp,0u,sp));
        assert(!predict_caller_stack_move(x(1,5,1,444),gp,0u,sp+8u));
        move=predict_caller_stack_move(x(8,5,8,444),gp,0x76543210u,sp,8);
        assert(move&&move->reg==5u&&move->value==sp+8u&&move->cr==0x76543210u);
        assert(!predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,7));
        assert(!predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,-1));
        assert(!predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,704));
        gp[8]=sp+704u;
        move=predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,704);
        assert(bool(move)==(sp+704u<0x81800000u));
        if(move)assert(move->value==sp+704u);
        gp[8]=sp-48u;
        move=predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,-48);
        assert(bool(move)==(sp>=0x80000030u));
        if(move)assert(move->value==sp-48u);
        assert(!predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,0x01800000));
        assert(!predict_caller_stack_move(x(8,5,8,444),gp,0u,sp,-0x01800000));
    }
    for(const auto sp:{0x7ffffff8u,0x80000001u,0x817ffd48u,0xfffffff8u}){
        gp[1]=sp;
        assert(!predict_caller_stack_move(x(1,5,1,444),gp,0u,sp));
    }
    unsigned relative_cases=0;
    for(const uint32_t sp:{0x80010000u,0x81000000u,0x817f0000u}){
        for(const int32_t offset:{-864,-48,0,704,864}){
            gp[1]=sp;gp[7]=uint32_t(int64_t(sp)+offset);
            const auto check=[&](uint32_t w,unsigned src,int32_t off,int64_t delta,unsigned dst,bool ok){
                const auto p=predict_caller_stack_relative(w,gp,0x12345678u,sp,src,off);
                assert(bool(p)==ok);
                if(p)assert(p->reg==dst&&p->value==uint32_t(int64_t(sp)+offset+delta)&&p->cr==0x12345678u);
                ++relative_cases;
            };
            check(d(14,6,7,12),7,offset,12,6,true);
            check(d(14,7,7,0xfff4),7,offset,-12,7,true);
            check(d(15,6,7,0xffff),7,offset,-65536,6,int64_t(sp)+offset-65536>=0x80000000ll);
            check(d(15,6,7,1),7,offset,65536,6,int64_t(sp)+offset+65536<0x81800000ll);
            check(x(7,6,7,444),7,offset,0,6,true);
            check(x(7,7,7,444),7,offset,0,7,true);
            check(d(14,6,7,12),6,offset,0,6,false);
            check(d(14,6,7,12),7,offset+1,0,6,false);
            check(d(14,1,7,12),7,offset,0,1,false);
            check(d(14,16,7,12),7,offset,0,16,false);
            check(d(14,6,0,12),0,offset,0,6,false);
            check(d(11,0,7,0),7,offset,0,0,false);
            check(d(32,6,7,0),7,offset,0,6,false);
            check(x(7,6,7,444,true),7,offset,0,6,false);
            check(x(7,6,8,444),7,offset,0,6,false);
            check(d(15,6,7,0x7fff),7,offset,0,6,false);
        }
    }
    assert(relative_cases==240);
    std::cout<<"FORMATTER_CALLER_INTEGER_TEST byte_patterns=256 stack_move_cases=64 stack_relative_cases="<<relative_cases<<" original_execution=0\n";
}
