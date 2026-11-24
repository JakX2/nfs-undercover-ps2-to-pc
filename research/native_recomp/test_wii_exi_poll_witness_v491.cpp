#include "wii_exi_poll_witness_v491.h"
#include "wii_exi_controller_v489.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("EXI poll witness");}
struct Mmu{std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr ExiColdPollExpectations e{{VectorEdge{0x804ef9bc,0x805208c8,1,2},
        VectorEdge{0x8052693c,0x804efa18,3,4}}};
    for(unsigned fault=0;fault<=10;++fault){
        exi_cold_poll_trace={};std::atomic<uint32_t> cause{0};WiiIrqBanks banks(cause);ExiController exi(banks);
        Cpu c;auto& m=c.mmu.mem;constexpr uint32_t sp=0x80751000;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        m[0x800000c4]=0xfffffff0;
        for(auto edge:e.edges){m[edge.pc]=edge.entry_word;m[edge.lr-4]=edge.branch_word;}
        auto enter=[&](unsigned i){c.pc=e.edges[i].pc;c.lr=e.edges[i].lr;++c.inst_count;};
        enter(0);ExiColdPollWitness w(e);need(w.begin(c,fault!=1)==(fault!=1));if(fault==1)continue;
        for(unsigned ch=0;ch<3;++ch){
            if(ch==2&&fault==2)continue;
            const uint32_t v=exi.read(ch,12);
            exi_cold_poll_trace.record(ch==1&&fault==3,12+20*ch+(ch==1&&fault==4?4u:0u),v|(ch==1&&fault==5?1u:0u));
        }
        if(fault==6)exi_cold_poll_trace.record(false,12,0);
        enter(1);c.gpr[1]-=32;c.gpr[3]=0x007f8000;m[sp+4]=0x805208c8;
        if(fault==7)c.gpr[3]^=1;
        if(fault==8)c.gpr[1]-=4;
        if(fault==9)m[sp+4]^=4;
        if(fault==10)m[0x800000c8]=1;
        const auto before=m;need(w.observe(c.pc,c)==(fault==0));need(before==m);
        if(!fault)need(w.stage()==2&&exi_cold_poll_trace.count()==3&&cause==0);else need(w.failure()!=0);
    }
    std::cout<<"PASS: native cold EXI poll sequence and 10 negative controls\n";
}
