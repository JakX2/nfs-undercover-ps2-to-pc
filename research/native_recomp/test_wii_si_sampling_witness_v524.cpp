#include "wii_si_sampling_witness_v524.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
static void need(bool b){if(!b)throw std::runtime_error("SI sample witness");}
struct Mmu{std::map<uint32_t,uint32_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=mem.find(a);return i==mem.end()?0:i->second;}};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000;bool is_running=true;uint64_t inst_count=1;};
int main(){
    constexpr uint32_t sp=0x80751000,r13=0x8070e8e0,id=0xbeef0010;
    constexpr SiSamplingExpectations e{{0x80532d6c,0x805320d4,1,2},{0x80536bf8,0x80532dac,3,4},
      {0x8053238c,0x80532e20,5,6},{0x805265f8,0x80532100,7,8},
      {0x805269bc,0x80532108,9,10},{0x80532aa8,0x80532110,11,12},0x000f0200};
    for(unsigned clock=0;clock<=1;++clock)for(unsigned fault=0;fault<=16;++fault){
        exi_id_completion={};si_sampling_trace={};need(exi_id_completion.begin(true));
        exi_id_completion.record({1,0,2,2,1,0},0);exi_id_completion.record({2,0,2,4,0,0},id);
        need(exi_id_completion.finish());
        Cpu c;auto& m=c.mmu.mem;c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=r13;c.gpr[3]=0;
        m[r13-3824]=id;m[0x80619a88]=e.table_word;m[0x80619a78]=8;m[0x806fe340]=0xffffffffu;
        for(auto x:{e.rate,e.tv,e.xy,e.handler,e.unmask,e.first_type}){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;++c.inst_count;};
        enter(e.rate);SiSamplingWitness w(e);need(w.begin(c,fault!=1,clock)==(fault!=1));if(fault==1)continue;
        enter(e.tv);c.gpr[1]=sp-32;if(fault==2)m[r13-3000]=1;
        need(w.observe(c.pc,c)==(fault!=2));if(fault==2)continue;
        si_sampling_trace.vi(fault==3,uint16_t(clock));
        enter(e.xy);c.gpr[3]=15*(1+clock);c.gpr[4]=2;if(fault==4)c.gpr[3]^=1;
        bool bad=fault==3||fault==4;need(w.observe(c.pc,c)==!bad);if(bad)continue;
        const uint32_t poll=(15u*(1u+clock)<<16)|0x200u;
        si_sampling_trace.si(true,SiController::Poll,poll^(fault==5?1u:0u));
        si_sampling_trace.si(false,SiController::Control,fault==6?1:0);
        if(fault!=7)si_sampling_trace.si(true,SiController::Control,SiController::TC_INT);
        enter(e.handler);c.gpr[1]=sp;c.gpr[3]=20;c.gpr[4]=0x80531b34u;m[0x80619a64]=poll;
        if(fault==8)c.gpr[4]^=4;
        bad=fault>=5&&fault<=8;need(w.observe(c.pc,c)==!bad);if(bad)continue;
        enter(e.unmask);c.gpr[3]=0x800;m[0x80003090]=fault==9?0:0x80531b34u;
        need(w.observe(c.pc,c)==(fault!=9));if(fault==9)continue;
        enter(e.first_type);c.gpr[3]=0;m[r13-3148]=fault==10?0:1;m[0xcc003004]=fault==11?0xf0:0xf8;
        if(fault==12)m[0x80003040]=1;
        if(fault==13)c.gpr[3]=1;
        if(fault==14)m[0x80619a64]^=1;
        if(fault==15)m[0x80619a78]=0;
        if(fault==16)m[0x806fe340]=0;
        need(w.observe(c.pc,c)==(fault==0));if(!fault)need(w.stage()==6);
        if(fault>=10){
            constexpr unsigned details[]{4,64,128,2,8,16,32};
            need(w.failure()==6&&w.detail()==details[fault-10]);
        }
    }
    std::cout<<"PASS: both VI clock selectors, original SI sampling/IRQ witness and 32 negative controls\n";
}
