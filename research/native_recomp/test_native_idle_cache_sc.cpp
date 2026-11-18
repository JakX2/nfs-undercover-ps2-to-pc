#include "native_idle_cache_sc.h"
#include <cassert>
#include <iostream>
struct Memory{
    std::array<uint8_t,8> bytes{};
    uint8_t read8(uint32_t p){return bytes.at(p-0x80000c00u);}
};
struct Context{
    Memory mmu;uint32_t msr=0,pc=0x80500000u,srr0=0,srr1=0,dispatch_saved_ctx=0;
};
int main(){
    constexpr std::array<uint8_t,8> expected{{1,2,3,4,5,6,7,8}};
    Context c;c.mmu.bytes=expected;unsigned calls=0;
    for(uint32_t bits:{0x2002u,0xa002u,0x8032u,0x8000u}){
        c.msr=bits;c.pc=0x80500000u;
        native_idle_cache_sc(c,0x80000c00u,expected,true,[&](Context& x){
            assert(x.pc==0x80000c00u&&x.srr0==0x80500004u&&x.srr1==bits);
            assert(!(x.msr&0x8000u)&&x.msr==(bits&~0xef33u));
            ++calls;x.pc=x.srr0;x.msr=x.srr1;
        });
        assert(c.pc==0x80500004u&&c.msr==bits);
    }
    auto reject=[&](bool idle){
        const auto prior=c;bool failed=false;
        try{native_idle_cache_sc(c,0x80000c00u,expected,idle,[&](Context&){++calls;});}
        catch(const std::runtime_error&){failed=true;}
        assert(failed&&c.pc==prior.pc&&c.msr==prior.msr&&c.srr0==prior.srr0&&calls==4);
    };
    reject(false);c.dispatch_saved_ctx=1;reject(true);c.dispatch_saved_ctx=0;
    c.mmu.bytes[0]=0;reject(true);c.mmu.bytes=expected;
    bool rejected_return=false;
    try{native_idle_cache_sc(c,0x80000c00u,expected,true,[](Context&){});}
    catch(const std::runtime_error&){rejected_return=true;}
    assert(rejected_return);
    std::cout<<"PASS: bounded native cache SC with MSR.EE restoration and pending interrupt refusal\n";
}
