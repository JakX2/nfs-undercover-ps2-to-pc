#include "wii_os_cache_reuse_v488.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("cache reuse");}
struct Mmu{std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000,
    hid0=0x1a00c200,l2cr=0x80001200,l2cr_busy_polls=0;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr OsCacheReuseExpectations e{{VectorEdge{0x80522540,0x805208c4,1,2},
        VectorEdge{0x804b7920,0x80522560,3,4},VectorEdge{0x804b7920,0x8052257c,5,4},
        VectorEdge{0x804b7930,0x80522598,7,8},VectorEdge{0x805230b8,0x80522654,9,10},
        VectorEdge{0x805265ac,0x805230e0,11,12},VectorEdge{0x805265d4,0x8052331c,13,14},
        VectorEdge{0x804e50b8,0x80522660,15,16},VectorEdge{0x804ef9bc,0x805208c8,17,18}}};
    for(unsigned fault=0;fault<=13;++fault){
        Cpu c;auto& m=c.mmu.mem;constexpr uint32_t sp=0x80751000,table=0x806f4f74;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        for(unsigned i=14;i<32;++i)c.gpr[i]=i*11;
        for(auto edge:e.edges){m[edge.pc]=edge.entry_word;m[edge.lr-4]=edge.branch_word;}
        m[table-4]=1;m[table]=0;m[table+4]=2;
        auto enter=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        enter(0);OsCacheReuseWitness w(e);
        if(fault==1)c.hid0^=0x4000;
        if(fault==2)c.l2cr&=0x7fffffff;
        if(fault==3)c.l2cr_busy_polls=1;
        need(w.begin(c)==!(fault>=1&&fault<=3));if(fault>=1&&fault<=3)continue;
        c.gpr[1]=sp-16;
        bool rejected=false;
        for(unsigned i=1;i<=8;++i){
            enter(i);
            if(i==4){c.gpr[3]=1;c.gpr[4]=0x805223f8;}
            if(i==5)c.gpr[1]=sp-48;
            if(i==6){m[table]=0x805223f8;c.gpr[3]=0;}
            if(i==7)c.gpr[1]=sp-16;
            if(i==8)c.gpr[1]=sp;
            bool bad=false;
            if(i==1&&fault==4){c.lr+=4;bad=true;}
            if(i==2&&fault==5){c.l2cr^=0x2000;bad=true;}
            if(i==3&&fault==6){c.hid0^=0x200;bad=true;}
            if(i==4&&fault==7){c.gpr[4]^=4;bad=true;}
            if(i==5&&fault==8){m[table]=3;bad=true;}
            if(i==6&&fault==9){m[table]=0;bad=true;}
            if(i==6&&fault==10){c.gpr[3]=1;bad=true;}
            if(i==7&&fault==11){m[table+4]=0;bad=true;}
            if(i==8&&fault==12){c.gpr[1]-=4;bad=true;}
            if(i==8&&fault==13){c.gpr[31]^=1;bad=true;}
            const auto before=m;need(w.observe(c.pc,c)==!bad);need(before==m);
            if(bad){rejected=true;break;}
        }
        need(fault?rejected&&w.failure()!=0:w.stage()==9);
    }
    std::cout<<"PASS: second original cache initializer reuse and 13 negative controls\n";
}
