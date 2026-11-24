#include "wii_alarm_startup_witness_v470.h"
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
static void need(bool ok){if(!ok)throw std::runtime_error("alarm witness");}
int main(){
    constexpr uint32_t sda=0x8070e8e0u,sp=0x80751c60u,dispatch=0x80003000u,
        node=0x8060bcb8u,aq=sda-3496u,sq=sda-3376u,handler=0x805217bcu;
    for(unsigned fault=0;fault<=15;++fault){
        Cpu c;auto& m=c.mmu.words;
        std::array<VectorEdge,5> e{{
            {0x805210ccu,0x805208b4u,1,11},{0x80520eb0u,0x805210e0u,2,12},
            {0x80520e9cu,0x80521108u,3,13},{0x80527b4cu,0x80521114u,4,14},
            {0x80526d30u,0x805208b8u,5,15}}};
        for(auto x:e){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        for(unsigned i=14;i<32;++i)c.gpr[i]=i*7u;
        m[sda-3552]=dispatch;
        for(unsigned i=0;i<15;++i)m[dispatch+4*i]=0x80520f5cu;
        m[dispatch+60]=0xa5a5a5a5u;
        m[node]=0x11111111u;m[node+4]=0x22222222u;m[node+16]=0x33333333u;
        m[aq]=m[aq+4]=0x44444444u;m[node+8]=m[node+12]=0x55555555u;
        auto set=[&](unsigned i){c.pc=e[i].pc;c.lr=e[i].lr;++c.inst_count;};
        AlarmStartupWitness witness(e);set(0);
        if(fault==1)m[sq]=node;
        if(fault==2)m[dispatch+32]=handler;
        auto snapshot=m;bool ok=witness.begin(c);need(m==snapshot);
        if(fault==1||fault==2){need(!ok&&witness.failure());continue;}need(ok);
        auto event=[&](unsigned i){set(i);auto before=m;bool pass=witness.observe(c.pc,c);need(before==m);return pass;};
        c.gpr[1]=sp-16;c.gpr[3]=8;
        if(fault==3)c.gpr[3]=7;
        if(fault==4)m[e[1].lr-4]=0;
        if(fault==5){need(!event(2));continue;}
        ok=event(1);if(fault==3||fault==4){need(!ok);continue;}need(ok);
        c.gpr[4]=handler;if(fault==6)c.gpr[4]++;
        if(fault==7)c.gpr[1]+=4;
        ok=event(2);if(fault==6||fault==7){need(!ok);continue;}need(ok);
        m[dispatch+32]=handler;m[aq]=m[aq+4]=0;c.gpr[3]=node;
        if(fault==8)m[dispatch+32]=0;
        if(fault==9)c.gpr[3]+=4;
        ok=event(3);if(fault==8||fault==9){need(!ok);continue;}need(ok);
        c.gpr[1]=sp;m[sq]=m[sq+4]=node;m[node+8]=m[node+12]=0;
        if(fault==10)m[dispatch+60]++;
        if(fault==11)m[node+4]++;
        if(fault==12)m[sq+4]=0;
        if(fault==13)c.gpr[14]++;
        if(fault==14)m[dispatch+12]=handler;
        if(fault==15){set(4);--c.inst_count;need(!witness.observe(c.pc,c));continue;}
        ok=event(4);need(ok==(fault==0));
        if(ok){need(witness.stage()==5&&witness.failure()==0);need(!event(4));}
        else need(witness.failure()!=0);
    }
    std::cout<<"PASS: cold alarm startup, module entry, 15 negative controls and observer memory preservation\n";
}
