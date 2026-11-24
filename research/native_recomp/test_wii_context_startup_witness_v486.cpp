#include "wii_context_startup_witness_v486.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("context startup");}
struct Mmu{
    std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    for(unsigned fault=0;fault<=12;++fault){
        constexpr ContextStartupExpectations e{{VectorEdge{0x80522eb8,0x805208c0,1,2},
            VectorEdge{0x80520e9c,0x80522ed4,3,4},VectorEdge{0x804e50b8,0x80522ef0,5,6},
            VectorEdge{0x80522540,0x805208c4,7,8}},16};
        Cpu c;auto& m=c.mmu.mem;c.gpr[1]=0x80751000;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        for(unsigned i=14;i<32;++i)c.gpr[i]=i*0x1234u;
        for(unsigned i=0;i<15;++i)m[0x80003000+4*i]=0x80520f5c;
        m[0x80003010]=0x80526ce0;m[0x80003020]=0x805217bc;m[0x8000303c]=123;
        m[0x800000d4]=456;m[0x800000d8]=789;m[0x800000dc]=321;
        for(auto edge:e.edges){m[edge.pc]=edge.entry_word;m[edge.lr-4]=edge.branch_word;}
        auto enter=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        enter(0);ContextStartupWitness w(e);if(fault==1)m[0x80003010]=0;
        need(w.begin(c)==(fault!=1));if(fault==1)continue;
        enter(1);c.gpr[1]-=16;c.gpr[3]=7;c.gpr[4]=0x80522e34;
        if(fault==2)c.gpr[3]=8;
        if(fault==3)c.gpr[1]-=8;
        if(fault==4)m[c.lr-4]^=1;
        need(w.observe(c.pc,c)==!(fault>=2&&fault<=4));if(fault>=2&&fault<=4)continue;
        enter(2);m[0x8000301c]=0x80522e34;
        if(fault==5)m[0x8000301c]=0;
        if(fault==6)m[0x80003020]=0;
        if(fault==7)c.lr+=4;
        need(w.observe(c.pc,c)==!(fault>=5&&fault<=7));if(fault>=5&&fault<=7)continue;
        enter(3);c.gpr[1]+=16;m[0x800000d8]=0;
        if(fault==8)m[0x800000d8]=1;
        if(fault==9)m[0x800000dc]=0;
        if(fault==10)c.gpr[14]=0;
        if(fault==11)m[0x8000303c]=0;
        if(fault==12)c.msr^=0x8000;
        const auto before=m;need(w.observe(c.pc,c)==(fault==0));need(before==m);
        if(!fault)need(w.stage()==4);else need(w.failure()!=0);
    }
    std::cout<<"PASS: original-free context initializer witness and 12 negative controls\n";
}
