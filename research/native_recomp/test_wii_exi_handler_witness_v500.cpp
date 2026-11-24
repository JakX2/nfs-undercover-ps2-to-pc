#include "wii_exi_handler_witness_v500.h"
#include "wii_exi_controller_v489.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI handler witness");}
struct Mmu{
    std::map<uint32_t,uint32_t> mem;uint8_t byte=0;ExiController& exi;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){if(a>=0xcd006800u&&a<0xcd00683cu)return exi.read((a-0xcd006800u)/20,(a-0xcd006800u)%20);auto i=mem.find(a);return i==mem.end()?0:i->second;}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr std::array<uint32_t,8> sites{0x804efa40,0x804efa50,0x804efa60,0x804efa6c,0x804efa78,0x804efa84,0x804efa90,0x804efa9c};
    constexpr std::array<uint32_t,8> handlers{0x804ef61c,0x804ef6d4,0x804ef8ec,0x804ef61c,0x804ef6d4,0x804ef8ec,0x804ef61c,0x804ef6d4};
    ExiHandlerExpectations e{};e.edges[0]={0x8052693c,0x804efa18,1,2};
    e.edges[1]={0x805265ac,0x8052695c,3,4};e.edges[2]={0x805265d4,0x8052699c,5,6};
    for(unsigned i=0;i<8;++i)e.edges[3+i]={0x805265f8,sites[i]+4,7+i,16};
    e.edges[11]={0x804efd7c,0x804efab0,17,18};
    for(unsigned fault=0;fault<=12;++fault){
        exi_mask_trace={};std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController exi(banks);
        Cpu c{{{},0,exi}};auto& m=c.mmu.mem;constexpr uint32_t sp=0x80751000,r13=0x8070e8e0;
        c.gpr[1]=sp;c.gpr[13]=r13;c.gpr[2]=0x80715ee0;c.gpr[3]=0x007f8000;
        m[0x800000c4]=0xfffffff0;m[r13-3408]=0x80003040;
        for(unsigned i=0;i<15;++i)m[0x80003000+i*4]=0x80520f5c;
        for(auto edge:e.edges){m[edge.pc]=edge.entry_word;m[edge.lr-4]=edge.branch_word;}
        auto enter=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        enter(0);ExiHandlerWitness w(e);if(fault==1)m[0x80003040]=1;
        need(w.begin(c)==(fault!=1));if(fault==1)continue;
        enter(1);c.gpr[1]-=32;if(fault==2)c.gpr[1]=sp;need(w.observe(c.pc,c)==(fault!=2));if(fault==2)continue;
        enter(2);c.gpr[3]=fault==3?1:0;need(w.observe(c.pc,c)==(fault!=3));if(fault==3)continue;
        c.gpr[1]=sp;
        for(unsigned i=0;i<4;++i){
            const unsigned ch=i==3?0:i;const uint32_t v=i==3?0x2000u:0;
            exi.write(ch,0,v);
            if(!(fault==4&&i==2))exi_mask_trace.record(!(fault==5&&i==1),ch*20,v);
        }
        bool rejected=false;
        for(unsigned i=0;i<8;++i){
            enter(3+i);c.gpr[3]=9+i;c.gpr[4]=handlers[i];
            if(fault==6&&i==2)c.gpr[4]^=4;
            if(fault==7&&i==1)m[0x80003040]=1;
            if(fault==8&&i==3)m[0x800000c8]=1;
            if(fault==9&&i==2)m[0x80003000]=0;
            if(fault==10&&i==4)m[0x80003040+4*(9+i-1)]=0;
            const bool bad=(i==0&&(fault==4||fault==5))||(i==2&&(fault==6||fault==9))||
                (i==1&&fault==7)||(i==3&&fault==8)||(i==4&&fault==10);
            need(w.observe(c.pc,c)==!bad);
            if(bad){rejected=true;break;}
            m[0x80003040+4*(9+i)]=handlers[i];
        }
        if(rejected)continue;
        enter(11);c.gpr[3]=0;c.gpr[4]=2;c.gpr[5]=r13-3824;
        if(fault==11)c.gpr[5]^=4;
        if(fault==12)m[0x806f1560]=1;
        need(w.observe(c.pc,c)==(fault==0));
        if(!fault)need(w.stage()==12&&exi_mask_trace.count()==4);
    }
    std::cout<<"PASS: EXI four native CSR writes, eight original handler-table registrations, uncached ID entry and 12 negative controls\n";
}
