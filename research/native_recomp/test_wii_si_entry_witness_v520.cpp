#include "wii_si_entry_witness_v520.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI entry witness");}
struct Mmu{std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr uint32_t sp=0x80751000,r13=0x8070e8e0,id=0xbeef0010,ev=0x80610000,sv=0x80611000;
    constexpr SiEntryExpectations e{{0x80521018,0x804efb60,1,2},{0x80532080,0x805208cc,3,4},
      {0x80521018,0x805320a0,5,2},{0x80532d6c,0x805320d4,6,7},0x48001edc,ev,sv};
    for(unsigned fault=0;fault<=12;++fault){
        exi_id_completion={};need(exi_id_completion.begin(true));
        exi_id_completion.record({1,0,2,2,1,0},0);exi_id_completion.record({2,0,2,4,0,0},id);
        need(exi_id_completion.finish());
        Cpu c;auto& m=c.mmu.mem;c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;c.gpr[3]=ev;
        m[r13-3824]=id;m[0x8070a748]=ev;m[0x8070aa70]=sv;m[0x80521024]=e.report_tail_word;
        for(auto x:{e.exi_version,e.si_entry,e.si_version,e.rate}){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;++c.inst_count;};
        enter(e.exi_version);SiEntryWitness w(e);
        if(fault==1)c.gpr[3]^=4;
        need(w.begin(c)==(fault!=1));
        if(fault==1)continue;
        auto tail=[&](uint32_t v){c.pc=0x80521024;c.gpr[3]=r13-16436u;c.gpr[4]=v;++c.inst_count;};
        tail(ev);
        if(fault==2)c.gpr[4]^=4;
        if(fault==3)c.lr^=4;
        bool bad=fault==2||fault==3;need(w.observe(c.pc,c)==!bad);if(bad)continue;
        enter(e.si_entry);c.gpr[1]=sp+32;
        if(fault==4)c.gpr[1]-=4;
        if(fault==5)m[r13-3148]=1;
        if(fault==6)m[r13-3824]^=4;
        bad=fault>=4&&fault<=6;need(w.observe(c.pc,c)==!bad);if(bad)continue;
        enter(e.si_version);c.gpr[1]=sp+16;c.gpr[3]=sv;
        if(fault==7)m[0x8070aa70]^=4;
        need(w.observe(c.pc,c)==(fault!=7));
        if(fault==7)continue;
        tail(sv);
        if(fault==8)c.gpr[3]^=4;
        if(fault==9)m[0x80521024]=0;
        bad=fault==8||fault==9;need(w.observe(c.pc,c)==!bad);if(bad)continue;
        enter(e.rate);c.gpr[3]=0;for(unsigned i=0;i<4;++i)m[0x806fe340u+32*i]=0xffffffffu;
        if(fault==10)m[0x806fe360]=0;
        if(fault==11)m[0x80003040]=1;
        if(fault==12)c.gpr[3]=1;
        need(w.observe(c.pc,c)==(fault==0));if(!fault)need(w.stage()==6);
    }
    std::cout<<"PASS: original EXI return and SI entry witness with 12 negative controls\n";
}
