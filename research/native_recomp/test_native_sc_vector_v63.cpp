#include "native_sc_vector_v63.h"
#include <cassert>
#include <iostream>
struct Memory{std::array<uint8_t,8> b{};uint8_t read8(uint32_t p){return b.at(p-0x1000u);}};
struct Context{Memory mmu;uint32_t msr=0x2002,pc=0x80004000,srr0=0,srr1=0,dispatch_saved_ctx=0;};
int main(){
    Context c;const std::array<uint8_t,8> expected{{1,2,3,4,5,6,7,8}};c.mmu.b=expected;
    unsigned calls=0;
    auto handler=[&](Context& x){assert(x.pc==0x1000&&x.srr0==0x80004004&&x.srr1==0x2002&&x.msr==0);
        ++calls;x.pc=x.srr0;x.msr=x.srr1;};
    boot_native_sc(c,0x1000,expected,handler);
    assert(calls==1&&c.pc==0x80004004&&c.msr==0x2002);
    auto reject=[&](){bool bad=false;try{boot_native_sc(c,0x1000,expected,handler);}catch(const std::runtime_error&){bad=true;}assert(bad&&calls==1);};
    c.mmu.b[2]=0;reject();c.mmu.b=expected;c.msr|=0x8000;reject();c.msr=2;c.dispatch_saved_ctx=1;reject();
    std::cout<<"PASS: native SC bounded exception entry, return and refusal guards\n";
}
