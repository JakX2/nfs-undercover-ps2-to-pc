#include "wii_module_irq_witness_v473.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint32_t read32(uint32_t a)const{auto p=words.find(a);return p==words.end()?0:p->second;}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;
    uint64_t inst_count=1;bool is_running=true;
};
static void need(bool ok){if(!ok)throw std::runtime_error("module IRQ witness");}
int main(){
    constexpr uint32_t sda=0x8070e8e0u,sp=0x80751c60u,t=0x80003040u,g=sda-3408u,
        mp=0x800030c4u,stop=0x8052664cu;
    for(unsigned fault=0;fault<=17;++fault){
        Cpu c;auto& m=c.mmu.words;
        ModuleIrqExpectations e{{{
            {0x80526d30u,0x805208b8u,1,11},{0x8052661cu,0x805208bcu,2,12},
            {0x8000443cu,stop,3,13},{0x80004388u,0x80004454u,4,14}}},0x99999999u};
        for(auto x:e.edges){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        m[stop]=e.return_word;c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        for(unsigned i=14;i<32;++i)c.gpr[i]=i*7u;
        m[t-4]=0xaaaaaaaau;m[t+128]=0xbbbbbbbbu;
        m[mp]=0xccccccccu;m[mp+16]=0xddddddddu;
        m[mp+4]=m[mp+8]=m[mp+12]=0x12345678u;
        for(unsigned i=0;i<32;++i)m[t+4*i]=0xf0000000u+i;
        auto set=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        auto snapshot=m;
        ModuleIrqWitness w(e);set(0);if(fault==1)c.gpr[13]++;
        bool ok=w.begin(c);need(m==snapshot);
        if(fault==1){need(!ok);continue;}need(ok);
        auto event=[&](unsigned i){set(i);auto before=m;bool pass=w.observe(c.pc,c);need(before==m);return pass;};
        m[mp+4]=m[mp+8]=m[mp+12]=0;
        if(fault==2)m[mp+4]=1;
        if(fault==3)m[mp+16]++;
        if(fault==4)c.gpr[14]++;
        if(fault==5)m[e.edges[1].lr-4]=0;
        ok=event(1);if(fault>=2&&fault<=5){need(!ok);continue;}need(ok);
        c.gpr[1]=sp-32;c.gpr[3]=t;c.gpr[4]=0;c.gpr[5]=128;m[g]=t;
        if(fault==6)c.gpr[5]=124;
        if(fault==7)m[g]=0;
        if(fault==8){need(!event(3));continue;}
        if(fault==9)c.gpr[1]+=4;
        ok=event(2);if(fault==6||fault==7||fault==9){need(!ok);continue;}need(ok);
        if(fault==10)m[e.edges[3].lr-4]=0;
        ok=event(3);if(fault==10){need(!ok);continue;}need(ok);
        for(unsigned i=0;i<32;++i)m[t+4*i]=0;
        c.pc=c.lr=stop;++c.inst_count;c.gpr[1]=sp-32;c.gpr[3]=t;
        if(fault==11)m[t+124]=1;
        if(fault==12)m[t-4]++;
        if(fault==13)m[t+128]++;
        if(fault==14)c.lr+=4;
        if(fault==15)c.gpr[3]+=4;
        if(fault==16)--c.inst_count;
        if(fault==17)m[stop]=0;
        snapshot=m;ok=w.observe(c.pc,c);need(m==snapshot);
        need(ok==(fault==0));
        if(ok){need(w.stage()==5);need(!w.observe(c.pc,c));}
        else need(w.failure()!=0);
    }
    std::cout<<"PASS: original-free module/IRQ table route and 17 negative controls\n";
}
