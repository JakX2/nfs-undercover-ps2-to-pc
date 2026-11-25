#include "wii_handler_index_branch_v911.h"
#include <cstdlib>
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,Table=0x80009000u,Nop=0x60000000u;
constexpr uint32_t Load=(31u<<26)|(5u<<21)|(3u<<16)|(4u<<11)|(23u<<1);
constexpr uint32_t Compare=(10u<<26)|(5u<<16)|7u,Branch=(16u<<26)|(12u<<21)|(2u<<16)|12u;
constexpr HandlerIndexBranchExpectation exp{H,Load,Compare,Branch,H+64u,{Table,Table+4u,Table+8u,Table+12u},20u};
struct CPU{
    struct MMU{
        std::map<uint32_t,uint8_t> data;
        const uint8_t* get_ptr(uint32_t a)const{auto i=data.find(a);return i==data.end()?nullptr:&i->second;}
        uint32_t read32(uint32_t a)const{uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|data.at(a+i);return v;}
        void put(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)data[a+i]=uint8_t(v>>(24u-8u*i));}
    }mmu;
    std::array<uint32_t,32> gpr{};
    struct Field{bool lt=false,gt=false,eq=false,so=false;};
    std::array<Field,8> cr{};
    uint32_t pc=H,ctr=123;
    uint64_t inst_count=100;
};
static void need(bool ok,const std::source_location l=std::source_location::current()){
    if(!ok){std::cerr<<"V911_TEST line="<<l.line()<<'\n';std::exit(1);}
}
int main(){
    unsigned good=0,bad=0;
    for(unsigned i=0;i<16;++i){
        CPU c;unsigned ch=i%4u;uint32_t value=(i&4u)?7u:9u;
        for(unsigned j=0;j<11;++j)c.mmu.put(H+4*j,Nop);
        c.mmu.put(H+44,Load);c.mmu.put(H+48,Compare);c.mmu.put(H+52,Branch);
        c.mmu.put(H+56,Nop);c.mmu.put(H+64,Nop);
        for(unsigned j=0;j<4;++j)c.mmu.put(Table+4*j,j==ch?value:0x12345678u+j);
        c.gpr[20]=ch;c.gpr[3]=Table;c.gpr[4]=4u*ch;
        HandlerIndexBranchWitness w(exp);
        if(i==8)c.gpr[20]=4;
        if(i==9)c.mmu.put(H+44,Load^1u);
        bool ok=w.start(c,H);
        if(i==8||i==9){need(!ok&&w.failure()==1u);++bad;continue;}
        need(ok);
        for(unsigned j=0;j<11;++j){need(w.before(c,H+4*j,Nop));++c.inst_count;}
        if(i==10)c.gpr[4]^=4u;
        ok=w.before(c,H+44,Load);
        if(i==10){need(!ok&&w.failure()==3u);++bad;continue;}
        need(ok);c.gpr[5]=value^(i==11);++c.inst_count;
        ok=w.before(c,H+48,Compare);
        if(i==11){need(!ok&&w.failure()==4u);++bad;continue;}
        need(ok);c.cr[0]={value<7u,value>7u,value==7u,false};++c.inst_count;
        if(i==12)c.cr[0].eq=!c.cr[0].eq;
        ok=w.before(c,H+52,Branch);
        if(i==12){need(!ok&&w.failure()==4u);++bad;continue;}
        need(ok);++c.inst_count;
        if(i==13)++c.ctr;
        if(i==14)++c.inst_count;
        const uint32_t dest=(value==7u)^(i==15)?H+64:H+56;
        ok=w.before(c,dest,Nop);
        if(i>=13){need(!ok);++bad;continue;}
        need(ok&&w.stage()==5u&&w.taken()==(value==7u));++good;
    }
    need(good==8u&&bad==8u);
    std::cout<<"V911_INDEX_BRANCH_WITNESS valid=8 refused=8 original_execution=0\n";
}
