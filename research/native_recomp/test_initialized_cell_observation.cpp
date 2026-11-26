#include "wii_initialized_cell_observation.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t A=0x80004000u;
struct Mmu {
    std::array<uint8_t,32> ram{};
    bool hole=false;
    uint8_t* get_ptr(uint32_t a){
        if(a<A||a>=A+ram.size()||(hole&&a==A+1))return nullptr;
        return ram.data()+a-A;
    }
};
struct Cpu{Mmu mmu;uint64_t inst_count=100;};
static void be(std::vector<uint8_t>& raw,unsigned at,uint32_t v){
    for(unsigned i=0;i<4;++i)raw.at(at+i)=uint8_t(v>>(24-8*i));
}
static std::vector<uint8_t> input(){
    std::vector<uint8_t> d(272,0);
    for(unsigned i=0;i<2;++i){
        be(d,0x1c+i*4,256+i*8);be(d,0x64+i*4,A+i*8);be(d,0xac+i*4,4);
    }
    d[256]=0x12;d[257]=0x34;d[258]=0x56;d[259]=0x78;
    return d;
}
int main(){
    const auto raw=input();
    assert(initialized_cell_bytes(raw,A,4)==(InitializedCellBytes{0x12,0x34,0x56,0x78}));
    assert(initialized_cell_bytes(raw,A+2,2)==(InitializedCellBytes{0x56,0x78,0,0}));
    assert(initialized_cell_bytes(raw,A+8,4)==InitializedCellBytes{});
    for(auto at:{A-4,A+1,A+4,A+12,0x81800000u})assert(!initialized_cell_bytes(raw,at,4));
    assert(!initialized_cell_bytes(raw,A,3));
    for(unsigned fault=0;fault<9;++fault){
        Cpu c;seed_initialized_dol_data(c.mmu,raw);
        if(fault==1)c.mmu.ram[0]=0;
        if(fault==7)c.mmu.hole=true;
        const auto initial=c.mmu.ram;
        InitializedCellObservation obs;
        const bool begun=obs.begin(c,raw,A,4);
        if(fault==7){assert(!begun);continue;}
        assert(begun&&c.mmu.ram==initial&&!obs.begin(c,raw,A,4));
        if(fault!=5)++c.inst_count;
        if(fault==2)c.mmu.ram[0]=0;
        if(fault==3){c.mmu.ram[0]=0;c.mmu.ram[0]=0x12;}
        if(fault==8)c.mmu.hole=true;
        const auto before=c.mmu.ram;
        Cpu other=c;
        const auto e=obs.finish(fault==4?other:c,fault!=6);
        if(fault>=4){assert(!e);continue;}
        assert(e&&e->pre_guest_matches_file==(fault!=1)&&e->boundary_matches_file==(fault==0||fault==3)&&e->sampled_values_equal==(fault!=2));
        assert(c.mmu.ram==before&&!obs.finish(c,true));
    }
    std::cout<<"INITIALIZED_CELL_OBSERVATION_TEST cases=9 endpoint_only=1 guest_writes=0 original_execution=0\n";
}
