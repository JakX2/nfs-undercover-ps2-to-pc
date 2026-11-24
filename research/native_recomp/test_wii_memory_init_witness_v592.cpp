#include "wii_memory_init_witness_v591.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
using W=MemoryInitWitness;
using B=BatMappingWitness;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V592 test line "+std::to_string(loc.line()));
}
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint32_t read32(uint32_t a){return words[a];}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{},bat_registers{};
    std::array<uint32_t,64> bat_write_sprs{},bat_write_values{};
    uint32_t pc=0,lr=0,msr=0x32u,srr0=0,srr1=0,dispatch_saved_ctx=0,bat_write_count=0,hid2=0x40001234;
    uint64_t inst_count=100;bool is_running=true;
    void write(uint32_t spr,uint32_t v){
        bat_registers[spr<=543?spr-528:16+spr-560]=v;
        bat_write_sprs[bat_write_count]=spr;bat_write_values[bat_write_count++]=v;
    }
};
int main(){
    MemoryInitExpectations e{};
    e.edges[0]={0x804b79dc,0x805208dc,1,2};
    e.edges[1]={0x804b79e4,0x805208e4,3,4};
    e.edges[2]={0x805276d4,0x805208f4,5,6};
    e.edges[3]={0x8052693c,0x80527718,7,8};
    for(unsigned i=0;i<5;++i)e.edges[4+i]={0x805265f8u,0x80527728u+12u*i,9u+i,14};
    e.edges[9]={0x80527b4c,0x80527764,15,16};
    e.edges[10]={0x80527568,0x80527770,17,18};
    e.edges[11]={0x805269bc,0x80527778,19,20};
    e.bat={e.edges[10],{{{0x80527550,B::Resume[0],21,22},{0x80527550,B::Resume[1],23,22}}},{24,25},{26,27}};
    e.entry_word=e.edges[0].branch_word;e.return_word=28;
    e.helpers.push_back({0x805266e0,0x80526970,29,30});
    constexpr uint32_t r13=0x8070e8e0,sp=ThreadInitWitness::StackTop-88;
    for(unsigned fault=0;fault<=18;++fault){
        std::atomic<uint32_t> pi{0x40};
        WiiIrqBanks banks(pi);IrqBankBinding binding(banks);
        Cpu c;W w(e);auto& m=c.mmu.words;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;
        c.pc=c.lr=W::Begin;m[W::Begin]=e.entry_word;m[W::Return]=e.return_word;
        m[0x800000e4]=ThreadInitWitness::Thread;m[ThreadInitWitness::StackBottom]=0xdeadbabe;
        m[r13-3376]=m[r13-3372]=W::AlarmNode;
        m[W::Node]=0x80527040;m[W::Node+4]=127;m[W::Node-4]=0xa1a1a1a1;m[W::Node+16]=0xb2b2b2b2;
        m[0x80003100]=m[0x80003104]=0x01800000;m[0x8000311c]=0x04000000;m[0x80003120]=0x93400000;
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;c.inst_count+=10;};
        if(fault==1)m[r13-3400]=1;
        if(fault==2)m[W::Node+8]=1;
        need(w.begin(c)==!(fault==1||fault==2));if(fault==1||fault==2)continue;
        enter(e.edges[0]);need(w.observe(c.pc,c));enter(e.edges[1]);c.gpr[3]=c.hid2&~0x40000000u;
        if(fault==3)c.gpr[3]^=1;
        need(w.observe(c.pc,c)==(fault!=3));if(fault==3)continue;
        enter(e.edges[2]);c.hid2=c.gpr[3];if(fault==4)c.hid2|=0x40000000;
        need(w.observe(c.pc,c)==(fault!=4));if(fault==4)continue;
        c.gpr[1]-=16;
        need(IrqBankBinding::write16(0xcc004020,0));
        if(fault!=5)need(IrqBankBinding::write16(0xcc004010,255));
        enter(e.edges[3]);c.gpr[3]=0xf0000000;
        need(w.observe(c.pc,c)==(fault!=5));if(fault==5)continue;
        enter(e.helpers[0]);if(fault==6)c.lr+=4;
        need(w.observe(c.pc,c)==(fault!=6));if(fault==6)continue;
        bool stopped=false;
        for(unsigned i=0;i<5;++i){
            enter(e.edges[4+i]);c.gpr[3]=i;c.gpr[4]=W::Handler;
            if(i==2&&fault==7)c.gpr[3]=1;
            if(i==2&&fault==8)m[W::IrqTable]=0;
            const bool bad=i==2&&(fault==7||fault==8);
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
            m[W::IrqTable+4*i]=W::Handler;
        }
        if(stopped)continue;
        enter(e.edges[9]);c.gpr[3]=W::Node;
        if(fault==9)c.gpr[3]+=4;
        need(w.observe(c.pc,c)==(fault!=9));if(fault==9)continue;
        m[r13-3372]=W::Node;m[W::AlarmNode+8]=W::Node;m[W::Node+12]=W::AlarmNode;
        enter(e.edges[10]);c.gpr[3]=0x000ba2cf;
        if(fault==10)m[W::Node+12]=0;
        need(w.observe(c.pc,c)==(fault!=10));if(fault==10)continue;
        for(unsigned lane=0;lane<2;++lane){
            enter(e.bat.trampoline[lane]);c.gpr[3]=B::Entry[lane];c.gpr[1]=sp-48;
            need(w.observe(c.pc,c));c.pc=B::Entry[lane];c.lr=B::Resume[lane];c.srr0=c.pc&0x3fffffff;
            c.srr1=c.msr=2;m[c.pc]=e.bat.entry_word[lane];c.inst_count+=10;
            if(!lane&&fault==11)c.srr0=c.pc;
            bool bad=!lane&&fault==11;
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
            for(unsigned i=lane?12:0;i<(lane?32:12);++i){auto [spr,v]=B::Writes[i];c.write(spr,v);}
            c.pc=c.lr=c.srr0=B::Resume[lane];c.srr1=c.msr=0x32;
            m[c.pc]=e.bat.return_word[lane];c.inst_count+=100;
            if(lane&&fault==12)c.bat_write_values[31]^=1;
            bad=lane&&fault==12;
            need(w.observe(c.pc,c)==!bad);if(bad){stopped=true;break;}
        }
        if(stopped)continue;
        enter(e.edges[11]);c.gpr[1]=sp-16;c.gpr[3]=0x08000000;
        if(fault==13)c.gpr[3]=0;
        need(w.observe(c.pc,c)==(fault!=13));if(fault==13)continue;
        need(IrqBankBinding::write16(0xcc00401c,fault==14?0:16));
        c.pc=c.lr=W::Return;c.gpr[1]=sp;c.inst_count+=10;m[r13-3400]=1;
        if(fault==15)m[r13-3400]=0;
        if(fault==16)m[W::Node+16]^=1;
        if(fault==17)m[ThreadInitWitness::StackBottom]=0;
        if(fault==18)c.gpr[1]-=4;
        need(w.observe(c.pc,c)==(fault==0));
        if(!fault){need(w.stage()==20&&pi.load()==0x40);need(!w.observe(c.pc,c));}
    }
    std::cout<<"V592_MI_WITNESS stages=20 positive=1 refused=18 bat=32 handlers=5 permissions=0\n";
}
