#include "wii_exi_id_witness_v504.h"
#include "wii_exi_endpoint_scheduler_v495.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI ID witness");}
struct Mmu{std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr ExiIdExpectations e{{VectorEdge{0x804efd7c,0x804efab0,1,2},
      VectorEdge{0x804efb80,0x804eff04,3,4},VectorEdge{0x804ee894,0x804efc58,5,6},
      VectorEdge{0x804ef3ec,0x804eff20,7,8},VectorEdge{0x804ee984,0x804eff4c,9,10},
      VectorEdge{0x804eed9c,0x804eff60,11,12},VectorEdge{0x80521008,0x804eef5c,13,14},
      VectorEdge{0x804ee984,0x804eff84,15,10},VectorEdge{0x804eed9c,0x804eff98,16,12},
      VectorEdge{0x80521008,0x804eef5c,13,14},VectorEdge{0x804ef51c,0x804effac,17,18},
      VectorEdge{0x804ee894,0x804effec,19,6}},20};
    for(unsigned fault=0;fault<=12;++fault){
        exi_id_completion={};Cpu c;auto& m=c.mmu.mem;
        constexpr uint32_t sp=0x80751000,r13=0x8070e8e0,cache=r13-3824,id=0xfeed1234;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;c.gpr[3]=0;c.gpr[4]=2;c.gpr[5]=cache;
        for(auto edge:e.edges){m[edge.pc]=edge.entry_word;m[edge.lr-4]=edge.branch_word;}m[0x804efab0]=20;
        auto enter=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        enter(0);ExiIdWitness w(e);need(w.begin(c,fault!=1)==(fault!=1));if(fault==1)continue;
        c.gpr[1]=sp-64;std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController exi(banks);
        ExiIdEndpoint endpoint(id);exi.attach(0,2,true);exi.write(0,0,0x200);
        auto transfer=[&](unsigned direction,unsigned length){
            exi.write(0,16,0);exi.write(0,12,((length-1)<<4)|(direction<<2)|1);
            const auto q=*exi.pending(0);endpoint.service(exi,q);
            if(!(fault==4&&direction==1))exi_id_completion.record(q,exi.read(0,16));
            if(fault==5&&direction==0)exi_id_completion.record(q,exi.read(0,16));
        };
        bool rejected=false;
        for(unsigned i=1;i<12;++i){
            enter(i);c.gpr[3]=0;
            if(i==1){c.gpr[4]=2;c.gpr[5]=0;}
            if(i==2||i==11)c.gpr[4]=0x806f1560;
            if(i==3){c.gpr[4]=2;c.gpr[5]=0;m[0x806f156c]=0x10;}
            if(i==4||i==7){c.gpr[4]=i==4?sp-32:cache;c.gpr[5]=i==4?2:4;c.gpr[6]=i==4?1:0;c.gpr[7]=0;m[0x806f156c]=0x14;}
            if(i==5||i==8){m[0x806f156c]=0x16;transfer(i==5?1:0,i==5?2:4);}
            if(i==10){m[cache]=id;m[0x806f156c]=0x14;}
            if(i==3&&fault==2)c.gpr[4]=1;
            if(i==4&&fault==3)c.gpr[5]=4;
            if(i==10&&fault==6)m[cache]^=1;
            if(i==11&&fault==7)c.gpr[4]=0;
            const bool bad=(i==3&&fault==2)||(i==4&&fault==3)||(i==6&&fault==4)||
                           (i==10&&fault==6)||(i==11&&fault==7);
            need(w.observe(c.pc,c)==!bad);if(bad){rejected=true;break;}
        }
        if(rejected)continue;
        c.pc=0x804efab0;c.gpr[1]=sp;c.gpr[3]=1;++c.inst_count;
        m[0x806f156c]=0;m[0x806f1570]=4;m[0x806f1574]=cache;m[0x806f1578]=2;
        if(fault==8)c.gpr[3]=0;
        if(fault==9)m[0x806f156c]=0x10;
        if(fault==10)m[0x80003040]=1;
        if(fault==11)c.gpr[1]-=4;
        if(fault==12)m[cache]^=1;
        need(w.observe(c.pc,c)==(fault==0));if(!fault)need(w.stage()==13);
    }
    std::cout<<"PASS: two genuine device completions, original ID cache and unlock witness, 12 negative controls\n";
}
