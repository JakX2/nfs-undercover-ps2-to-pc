#include "wii_word_mmio_v1294.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
struct Cpu{std::array<uint32_t,32> gpr{};};
int main(){
    constexpr uint32_t Base=0x0d000000u, Alias=Base|0xc0000000u, Reply=0x12345678u;
    auto d=[](unsigned op,unsigned r,unsigned a,unsigned off){return (op<<26)|(r<<21)|(a<<16)|off;};
    auto x=[](unsigned xo,unsigned r,unsigned a,unsigned b){return (31u<<26)|(r<<21)|(a<<16)|(b<<11)|(xo<<1);};
    unsigned n=0;
    for(unsigned op:{32u,33u,36u,37u}){
        Cpu c;c.gpr[4]=Alias;c.gpr[3]=0xabcdef01u;
        const auto q=WordMmioInstruction::decode(c,d(op,3,4,4));
        assert(q.targets_window(Base,0x40u)&&!q.targets_window(Base+0x40u,0x40u));
        if(op<36u){assert(!q.completed(c,Reply));c.gpr[3]=Reply;}
        if(op&1u){assert(!q.completed(c,Reply));c.gpr[4]=Alias+4u;}
        assert(q.completed(c,Reply));++n;
    }
    for(unsigned xo:{23u,55u,151u,183u,534u,662u}){
        Cpu c;c.gpr[4]=Alias;c.gpr[5]=8u;
        const auto q=WordMmioInstruction::decode(c,x(xo,3,4,5));
        assert(q.targets_window(Base,0x40u));
        if(xo==23u||xo==55u||xo==534u){assert(!q.completed(c,Reply));c.gpr[3]=xo==534u?0x78563412u:Reply;}
        if(xo==55u||xo==183u){assert(!q.completed(c,Reply));c.gpr[4]=Alias+8u;}
        assert(q.completed(c,Reply));++n;
    }
    Cpu c;c.gpr[4]=Alias-2u;
    assert(WordMmioInstruction::decode(c,d(32,3,4,0)).targets_window(Base,0x40u));++n;
    c.gpr[4]=Alias+0x40u;assert(!WordMmioInstruction::decode(c,d(32,3,4,0)).targets_window(Base,0x40u));++n;
    c.gpr[4]=0x4d000004u;const auto bad=WordMmioInstruction::decode(c,d(32,3,4,0));
    assert(bad.targets_window(Base,0x40u)&&!bad.address(Base+4u));++n;
    const auto nop=WordMmioInstruction::decode(c,0x60000000u);assert(!nop.completed(c,0)&&!nop.targets_window(Base,0x40u));++n;
    assert(n==14u);std::cout<<"V1296_MMIO_COMPLETION synthetic=1 cases=14 readback=1 update=1 original_execution=0\n";
}
