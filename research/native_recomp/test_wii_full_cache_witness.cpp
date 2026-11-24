#include "wii_full_cache_witness.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
using R=FullStartResult;
struct Mmu {
    std::map<uint32_t,uint32_t> mem;
    uint32_t* get_ptr(uint32_t a){auto it=mem.find(a&~3u);return it==mem.end()?nullptr:&it->second;}
    uint32_t read32(uint32_t a){return mem.at(a);}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=0x80522540u,lr=0,msr=0xa000u,hid0=0x800u,l2cr=0x1200u,l2cr_busy_polls=0;
    uint64_t inst_count=100;bool is_running=true;
};
static void need(bool v,const char* s){if(!v)throw std::runtime_error(s);}
int main(){
    constexpr uint32_t table=0x806f4f74u,sp=0x80751cb8u,handler=0x805223f8u;
    CacheExpectations e{};
    const std::array<uint32_t,9> targets{0x804b7920u,0x805223bcu,0x80522280u,0x804b7930u,0x804b7938u,0x804b7910u,0x804b7918u,0x804e50b8u,0x805230b8u};
    for(unsigned i=0;i<26;++i)e.cache[i]={targets[i%9],0x80522544u+4u*i,0x48000001u+i,0x60000000u};
    e.error={CacheEdge{0x805265acu,0x805230e0u,1u,2u},CacheEdge{0x805265d4u,0x8052331cu,3u,4u}};
    e.data={0x80004238u,0x80004058u,5u,6u};
    for(unsigned mode=0;mode<8;++mode)for(unsigned fault=0;fault<8;++fault){
        Cpu c;c.gpr[1]=sp;c.gpr[4]=handler;c.gpr[3]=1u;
        if(mode&1u)c.hid0|=0x8000u;
        if(mode&2u)c.hid0|=0x4000u;
        if(mode&4u)c.l2cr|=0x80000000u;
        for(auto a:{table-4u,table,table+4u,sp-8u,sp-4u,handler})c.mmu.mem[a]=0x12345678u;
        auto load=[&](const CacheEdge& a){c.mmu.mem[a.pc]=a.entry_word;c.mmu.mem[a.lr-4u]=a.branch_word;};
        for(auto a:e.cache)load(a);
        for(auto a:e.error)load(a);
        load(e.data);
        FullCacheWitness w(e);need(w.begin(c),"begin");
        auto enter=[&](const CacheEdge& a){c.pc=a.pc;c.lr=a.lr;c.inst_count+=5;return w.observe(c.pc,c);};
        need(enter(e.cache[0])==R::Accepted,"first helper");
        if(!(mode&1u))need(enter(e.cache[1])==R::Accepted,"ICE");
        if(!(mode&2u))need(enter(e.cache[2])==R::Accepted,"DCE");
        need(enter(e.cache[3])==R::Accepted,"L2 read");
        if(!(mode&4u))for(unsigned i=0;i<5;++i)need(enter(e.cache[4])==R::Accepted,"L2 write");
        c.hid0|=0xc000u;c.l2cr|=0x80000000u;
        if(fault==1)c.hid0^=0x4000u;
        if(fault==2)c.mmu.mem[e.cache[8].lr-4u]^=1u;
        if(fault==3)c.gpr[3]=2u;
        auto r=enter(e.cache[8]);
        if(fault>=1&&fault<=3){need(r==R::Invalid&&w.stage()==0,"invalid cache state accepted");continue;}
        need(r==R::Accepted&&w.stage()==1,"handler entry");
        if(fault==4)c.mmu.mem[table]^=1u;
        r=enter(e.error[0]);
        if(fault==4){need(r==R::Invalid&&w.stage()==1,"changed initial table accepted");continue;}
        need(r==R::Accepted&&w.stage()==2,"disable entry");
        c.msr&=~0x8000u;c.mmu.mem[table]=handler;
        if(fault==5)c.mmu.mem[table+4u]^=1u;
        if(fault==6)c.msr|=0x8000u;
        r=enter(e.error[1]);
        if(fault==5||fault==6){need(r==R::Invalid&&w.stage()==2,"bad restore accepted");continue;}
        need(r==R::Accepted&&w.stage()==3,"restore entry");
        c.msr=0xa000u;c.gpr[1]=sp-8u;c.mmu.mem[sp-8u]=c.mmu.mem[sp-4u]=0xffffffffu;
        if(fault==7)c.mmu.mem[sp-4u]=0;
        r=enter(e.data);
        need(fault==7?(r==R::Invalid&&w.stage()==3):(r==R::Complete&&w.stage()==4),"bad data entry classification");
    }
    std::cout<<"PASS: cache witness across eight initial cache states and 56 negative cases\n";
}
