#include "wii_audio_reset_witness_v556.h"
#include "v556_test_acr.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("audio reset witness line "+std::to_string(loc.line()));
}
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint32_t read32(uint32_t a){auto i=words.find(a);return i==words.end()?0:i->second;}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=2;
    bool is_running=true;uint64_t inst_count=0xfffff000u;
    uint64_t read_timebase()const{return inst_count;}
};
int main(){
    using W=AudioResetWitness;using A=AudioAcrBinding;
    constexpr uint32_t sp=ThreadInitWitness::StackTop-88u;
    constexpr std::array<uint32_t,10> lrs{0x80521e18u,0x80521e2cu,0x80521ea8u,0x80521ebcu,
        0x80521ef4u,0x80521f08u,0x80521f44u,0x80521f58u,0x80521f94u,0x80521fa8u};
    AudioResetExpectations e{{0x80521fecu,0x805208d8u,1,2},{0x80521dccu,0x80522010u,3,4},{},5};
    for(unsigned i=0;i<10;++i)e.time[i]={0x8052a83cu,lrs[i],10+i,6};
    for(unsigned fault=0;fault<=18;++fault){
        audio_reset_trace={};
        Cpu c;auto& m=c.mmu.words;c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        auto seed=[&](VectorEdge x){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;};
        seed(e.audio);seed(e.reset);for(auto x:e.time)seed(x);
        m[W::Return]=e.return_word;m[0x800000e4u]=ThreadInitWitness::Thread;
        m[ThreadInitWitness::StackBottom]=0xdeadbabeu;m[sp-16]=sp;
        c.pc=e.audio.lr-4;
        A acr({0x12345680u,0xa955aa55u,0xf1234567u});
        W w(e);need(w.begin(c,fault!=1)==(fault!=1));if(fault==1)continue;
        auto enter=[&](VectorEdge x){c.pc=x.pc;c.lr=x.lr;};
        enter(e.audio);c.inst_count+=8;
        if(fault==2)c.lr^=4;
        need(w.observe(c.pc,c)==(fault!=2));if(fault==2)continue;
        enter(e.reset);c.gpr[1]=sp-16;c.gpr[3]=fault==3?0:1;c.inst_count+=8;
        need(w.observe(c.pc,c)==(fault!=3));if(fault==3)continue;
        auto rmw=[&](unsigned i){
            const uint32_t reg=AudioResetTrace::Registers[i];const auto read=*A::read32(reg);
            uint32_t value=read;
            switch(i){case 0:value=(read|0x100u)&~0x80u;break;
            case 1:value=read&0x3fffffffu;break;
            case 2:value=(read&0xf8000000u)|0x04b0ffceu;break;
            case 3:value=read&~0x10000000u;break;
            case 4:value=read|0x40000000u;break;
            case 5:value=read|0x80000000u;break;}
            if(fault==5&&i==0)value^=0x80u;
            need(A::write32(reg,value));
        };
        if(fault==4){(void)A::read32(A::Pll);}
        rmw(0);rmw(1);c.gpr[1]=sp-48;
        enter(e.time[0]);c.inst_count+=8;
        if(fault==6)c.lr^=4;
        if(fault==13)c.msr^=2;
        if(fault==14)c.gpr[1]-=4;
        const bool initial_bad=fault==4||fault==5||fault==6||fault==13||fault==14;
        need(w.observe(c.pc,c)==!initial_bad);if(initial_bad)continue;
        bool rejected=false;
        for(unsigned i=0;i<5&&!rejected;++i){
            if(i){
                rmw(i+1);enter(e.time[2*i]);c.inst_count+=8;
                need(w.observe(c.pc,c));
            }
            enter(e.time[2*i+1]);
            if(i==0&&fault==7){
                c.inst_count+=32;need(w.observe(c.pc,c));
                // Read next ACR before the previous interval completed.
                (void)A::read32(A::Pll);c.inst_count+=32;
                need(!w.observe(c.pc,c));rejected=true;break;
            }
            if(i==0&&(fault==8||fault==9)){
                if(fault==9)c.inst_count+=65;
                need(!w.observe(c.pc,c));rejected=true;break;
            }
            for(unsigned delta=0;delta<AudioResetTrace::Minimum[i];delta+=32){
                c.inst_count+=32;need(w.observe(c.pc,c));
            }
            need(w.stage()==4+i);
            if(i==0&&fault==10){
                c.inst_count+=32;need(!w.observe(c.pc,c));rejected=true;
            }
            if(i==0&&fault==11){
                (void)A::read32(A::Pll);(void)A::read32(A::Pll);
                c.inst_count+=32;need(!w.observe(c.pc,c));rejected=true;
            }
            if(i==0&&fault==12){
                rmw(2);(void)A::read32(A::Ext);
                enter(e.time[2]);c.inst_count+=32;need(!w.observe(c.pc,c));rejected=true;
            }
            if(i==3&&fault==18)break;
        }
        if(rejected)continue;
        c.pc=W::Return;c.lr=W::Return;c.gpr[1]=sp-16;c.inst_count+=8;
        if(fault==15)m[ThreadInitWitness::StackBottom]=0;
        if(fault==16)c.gpr[14]=1;
        if(fault==17)m[W::Return]=0;
        need(w.observe(c.pc,c)==(fault==0));if(!fault)need(w.stage()==9&&audio_reset_trace.waits()==5);
    }
    std::cout<<"PASS: actual ACR read/modify/write trace, five virtual guest timebase delays (including wrap), 18 negative controls\n";
}
