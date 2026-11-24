#include "wii_exi_absent_witness_v510.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI absent witness");}
struct Mmu{std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr uint32_t sp=0x80751000,r13=0x8070e8e0,id=0xbeef0010,version=0x80610000;
    constexpr ExiAbsentExpectations e{{VectorEdge{0x804efd7c,0x804efafc,1,2},VectorEdge{0x804efd7c,0x804efb34,3,2},
      VectorEdge{0x804ef09c,0x804efdec,4,5},VectorEdge{0x805265ac,0x804ef0e4,6,7},
      VectorEdge{0x805265d4,0x804ef1f8,8,9}},VectorEdge{0x80521018,0x804efb60,10,11},12,{13,14},version};
    for(unsigned fault=0;fault<=12;++fault){
        exi_id_completion={};exi_absent_trace={};
        need(exi_id_completion.begin(true));exi_id_completion.record({1,0,2,2,1,0},0);
        exi_id_completion.record({2,0,2,4,0,0},id);need(exi_id_completion.finish());
        Cpu c;auto& m=c.mmu.mem;c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;c.gpr[3]=1;
        m[r13-3824]=id;m[0x804efab0]=12;m[0x804efafc]=13;m[0x804efb34]=14;m[0x8070a748]=version;
        for(auto x:e.edges){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        m[e.version.pc]=e.version.entry_word;m[e.version.lr-4]=e.version.branch_word;
        ExiAbsentWitness w(e);if(fault==1)m[r13-3824]^=1;
        need(w.begin(c)==(fault!=1));if(fault==1)continue;
        bool rejected=false;auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;++c.inst_count;};
        for(unsigned ch=0;ch<2;++ch){
            enter(e.edges[ch]);c.gpr[1]=sp;c.gpr[3]=ch;c.gpr[4]=0;c.gpr[5]=sp+8;
            if(fault==2&&ch==0)c.gpr[4]=1;
            bool bad=fault==2&&ch==0;need(w.observe(c.pc,c)==!bad);if(bad){rejected=true;break;}
            enter(e.edges[2]);c.gpr[1]=sp-64;
            if(fault==3&&ch==0)c.gpr[3]=1;
            bad=fault==3&&ch==0;need(w.observe(c.pc,c)==!bad);if(bad){rejected=true;break;}
            if(fault==4&&ch==0)exi_absent_trace.mmio(false,20,0);
            else if(!(fault==5&&ch==0))exi_absent_trace.mmio(false,ch*20,ch==0?8u:0u);
            if(fault==6&&ch==0)exi_absent_trace.mmio(true,0,0);
            if(fault==7&&ch==0)exi_absent_trace.completion();
            c.pc=ch?0x804efb34:0x804efafc;c.gpr[1]=sp;c.gpr[3]=0;++c.inst_count;
            if(fault==8&&ch==1)c.gpr[3]=1;
            if(fault==9&&ch==1)m[0x800030c4]=1;
            bad=(ch==0&&(fault==4||fault==5))||(ch==1&&(fault==8||fault==9));
            need(w.observe(c.pc,c)==!bad);if(bad){rejected=true;break;}
        }
        if(rejected)continue;
        enter(e.version);c.gpr[3]=version;
        if(fault==10)c.gpr[3]^=4;
        if(fault==11)m[0x80003040]=1;
        if(fault==12)m[0x8070a748]^=4;
        need(w.observe(c.pc,c)==(fault==0));if(!fault)need(w.stage()==8);
    }
    std::cout<<"PASS: absent-card original ID return witness, sticky TC status, version entry and 12 negative controls\n";
}
