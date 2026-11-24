#include "wii_bat_mapping_witness_v590.h"
#include <map>
#include <iostream>
#include <source_location>
using namespace undercover::wii;
using W=BatMappingWitness;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V590 test line "+std::to_string(loc.line()));
}
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint32_t read32(uint32_t a){return words[a];}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{},bat_registers{};
    std::array<uint32_t,64> bat_write_sprs{},bat_write_values{};
    uint32_t pc=0,lr=0,msr=0x32u,srr0=0,srr1=0,dispatch_saved_ctx=0,bat_write_count=0;
    uint64_t inst_count=100;bool is_running=true;
    void write(uint32_t spr,uint32_t v){
        bat_registers[spr<=543?spr-528:16+spr-560]=v;
        bat_write_sprs[bat_write_count]=spr;bat_write_values[bat_write_count++]=v;
    }
};
int main(){
    BatMappingExpectations e{{0x80527568,0x80527770,1,2},
        {{{0x80527550,W::Resume[0],3,4},{0x80527550,W::Resume[1],5,4}}},{6,7},{8,9}};
    for(unsigned fault=0;fault<=20;++fault){
        W w(e);Cpu c;
        c.gpr[1]=0x80751c20;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        for(unsigned i=0;i<32;++i)c.bat_registers[i]=0xabcd0000u+i;
        c.write(543,0xcafebabe);c.write(563,0x1234);
        auto edge=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;c.mmu.words[x.pc]=x.entry_word;c.mmu.words[x.lr-4]=x.branch_word;c.inst_count+=10;};
        c.mmu.words[0x80003100]=c.mmu.words[0x80003104]=0x01800000;
        c.mmu.words[0x8000311c]=0x04000000;c.mmu.words[0x80003120]=0x93400000;
        edge(e.mapper);c.gpr[3]=0x000ba2cf;
        if(fault==1)c.gpr[3]^=1;
        if(fault==2)c.mmu.words[0x80003120]=0;
        if(fault==3)c.msr&=~0x30u;
        const auto mask=w.entry_failures(c,fault!=4);
        constexpr std::array<uint32_t,5> expected{0,1u<<4,1u<<11,1u<<6,1u<<1};
        need(mask==(fault<=4?expected[fault]:0u));
        if(fault==0){
            auto f=c;f.bat_write_count=33;f.msr|=0x8000u;
            need(w.entry_failures(f,true)==((1u<<12)|(1u<<5)));
            f=c;f.dispatch_saved_ctx=1;need(w.entry_failures(f,true)==(1u<<7));
            f=c;f.lr+=4;need(w.entry_failures(f,true)==(1u<<3));
        }
        bool bad=fault>=1&&fault<=4;
        need(w.begin(c,fault!=4)==!bad);if(bad)continue;
        bool stopped=false;
        for(unsigned lane=0;lane<2;++lane){
            edge(e.trampoline[lane]);c.gpr[3]=W::Entry[lane];
            if(!lane)c.gpr[1]-=16;
            if(!lane&&fault==5)c.gpr[3]+=4;
            if(!lane&&fault==6)c.lr+=4;
            if(!lane&&fault==7)c.inst_count-=10;
            bad=!lane&&fault>=5&&fault<=7;
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
            c.pc=W::Entry[lane];c.lr=W::Resume[lane];c.srr0=c.pc&0x3fffffff;
            c.srr1=c.msr=2;c.mmu.words[c.pc]=e.entry_word[lane];c.inst_count+=10;
            if(!lane&&fault==8)c.srr0=c.pc;
            if(!lane&&fault==9)c.msr|=0x30;
            if(!lane&&fault==10)c.mmu.words[c.pc]=0;
            if(!lane&&fault==11)c.dispatch_saved_ctx=1;
            bad=!lane&&fault>=8&&fault<=11;
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
            for(unsigned i=lane?12:0;i<(lane?32:12);++i){auto [spr,v]=W::Writes[i];c.write(spr,v);}
            c.pc=c.lr=c.srr0=W::Resume[lane];c.srr1=c.msr=0x32;
            c.mmu.words[c.pc]=e.return_word[lane];c.inst_count+=100;
            if(!lane&&fault==12)c.bat_write_sprs[2]^=1;
            if(!lane&&fault==13)c.bat_write_values[3]^=1;
            if(!lane&&fault==14)c.bat_registers[15]^=1;
            if(!lane&&fault==15)c.srr1^=0x20;
            if(!lane&&fault==16)c.gpr[1]+=4;
            if(lane&&fault==17)c.bat_write_count--;
            if(lane&&fault==18)c.mmu.words[c.pc]=0;
            bad=(!lane&&fault>=12&&fault<=16)||(lane&&(fault==17||fault==18));
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
        }
        if(stopped)continue;
        need(w.stage()==7);
        if(fault==19)c.bat_registers[0]^=1;
        if(fault==20)c.gpr[13]^=4;
        need(w.final_state(c)==(fault==0));
        if(!fault)need(!w.observe(c.pc,c));
    }
    std::cout<<"V590_BAT_MAPPING positive=1 writes=32 physical_entries=2 returns=2 refused=20 prior_state=1 permissions=0\n";
}
