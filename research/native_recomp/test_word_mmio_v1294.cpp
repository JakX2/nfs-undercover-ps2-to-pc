#include "wii_word_mmio_v1294.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
struct Cpu{std::array<uint32_t,32> gpr{};};
int main(){
    Cpu c;c.gpr[4]=0xcd000010u;c.gpr[3]=0x12345678u;c.gpr[5]=0xfffffff4u;
    auto d=[](unsigned op,unsigned rs,unsigned ra,unsigned off){return (op<<26)|(rs<<21)|(ra<<16)|off;};
    auto x=[](unsigned xo,unsigned rs,unsigned ra,unsigned rb){return (31u<<26)|(rs<<21)|(ra<<16)|(rb<<11)|(xo<<1);};
    using K=WordMmioInstruction::Kind;unsigned n=0;
    for(unsigned op:{32u,33u,36u,37u}){
        auto q=WordMmioInstruction::decode(c,d(op,3,4,0xfff4u));
        assert(q.kind==(op<36?K::Read:K::Write)&&q.address(0x0d000004u)&&q.address(0xcd000004u)&&
            !q.address(0x0d000008u)&&!q.address(0x4d000004u));
        assert(q.form==((op&1u)?3u:1u));if(op>=36)assert(q.value==c.gpr[3]);++n;
    }
    for(unsigned xo:{23u,55u,151u,183u,534u,662u}){
        auto q=WordMmioInstruction::decode(c,x(xo,3,4,5));
        const bool read=xo==23||xo==55||xo==534;
        assert(q.kind==(read?K::Read:K::Write)&&q.address(0x0d000004u));
        assert(q.form==(xo==534||xo==662?4u:xo==55||xo==183?3u:2u));
        if(!read)assert(q.value==(xo==662?0x78563412u:0x12345678u));++n;
    }
    c.gpr[0]=0xdeadbeefu;c.gpr[5]=0xcd000004u;
    auto q=WordMmioInstruction::decode(c,x(151,3,0,5));assert(q.address(0x0d000004u));++n;
    for(auto w:{d(33,3,0,0),d(33,3,3,0),d(37,3,0,0),x(55,3,3,5),x(183,3,0,5),x(151,3,4,5)|1u,0x60000000u}){
        assert(WordMmioInstruction::decode(c,w).kind==K::None);++n;
    }
    c.gpr[4]=0x4d000004u;assert(!WordMmioInstruction::decode(c,d(36,3,4,0)).address(0x0d000004u));++n;
    c.gpr[4]=0xcd000005u;assert(!WordMmioInstruction::decode(c,d(36,3,4,0)).address(0x0d000004u));++n;
    assert(n==20u);std::cout<<"V1294_MMIO_DECODE synthetic=1 cases=20 exact_ea=1 exact_store=1 original_execution=0\n";
}
