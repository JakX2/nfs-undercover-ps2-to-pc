#include "flat_cacheline_zero_v67.h"
#include <array>
#include <cassert>
#include <iostream>
struct FakeMmu {
    std::array<uint8_t,128> mem1{};
    std::array<uint8_t,64> mem2{};
    uint8_t* get_ptr(uint32_t address){
        const uint32_t p=address&0x3fffffffu;
        if(p<mem1.size())return mem1.data()+p;
        if(p>=0x10000000u&&p<0x10000000u+mem2.size())return mem2.data()+p-0x10000000u;
        return nullptr;
    }
};
int main(){
    using nwii::runtime::FlatCachelineZeroTrace;
    FakeMmu m;FlatCachelineZeroTrace trace;
    for(unsigned offset=0;offset<32;++offset){
        m.mem1.fill(0xa5);trace.clear();
        const uint32_t alias=(offset%3u==0?0u:offset%3u==1?0x80000000u:0xc0000000u);
        trace.zero(m,alias+32u+offset);
        assert(trace.count==1&&trace.first==alias+32u&&trace.last==trace.first);
        for(unsigned i=0;i<m.mem1.size();++i)assert(m.mem1[i]==(i>=32u&&i<64u?0u:0xa5u));
    }
    m.mem2.fill(0x7d);trace.clear();trace.zero(m,0x90000000u+31u);trace.zero(m,0xd0000000u+63u);
    assert(trace.count==2&&trace.first==0x90000000u&&trace.last==0xd0000020u);
    for(auto v:m.mem2)assert(v==0);
    for(uint32_t ea:{0x0c00500au,0x0d800000u,0x80000080u,0x94000000u,0xffffffffu}){
        const auto prior=trace;const auto prev1=m.mem1;const auto prev2=m.mem2;
        bool rejected=false;
        try{trace.zero(m,ea);}catch(const std::runtime_error&){rejected=true;}
        assert(rejected&&trace.count==prior.count&&trace.first==prior.first&&trace.last==prior.last&&m.mem1==prev1&&m.mem2==prev2);
    }
    std::cout<<"PASS: 32 offsets, 3 aliases, MEM2 and 5 fail-closed dcbz cases\n";
}
