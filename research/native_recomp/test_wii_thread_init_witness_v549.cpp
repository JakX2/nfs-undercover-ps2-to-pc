#include "wii_thread_init_witness_v549.h"
#include <iostream>
#include <map>
#include <source_location>
using namespace undercover::wii;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("thread witness line "+std::to_string(loc.line()));
}
struct Mmu {
    std::map<uint32_t,uint32_t> words;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint32_t read32(uint32_t a){auto i=words.find(a);return i==words.end()?0:i->second;}
    uint8_t read8(uint32_t a){return uint8_t(read32(a&~3u)>>(24u-8u*(a&3u)));}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x2000,ctr=0;
    bool is_running=true;uint64_t inst_count=10000;
};
int main(){
    using W=ThreadInitWitness;
    constexpr uint32_t sp=W::StackTop-88u,frame=sp-32u;
    constexpr ThreadInitExpectations e{{0x8052912c,0x805208d4,1,2},{0x80522af4,0x805291a0,3,4},
        {0x805228cc,0x805291a8,5,6},{0x80529128,0x805291e0,7,8},
        {0x80522a8c,0x805291e8,9,10},{0x80522af4,0x80529390,11,4},12};
    const std::array<VectorEdge,6> edges{e.thread,e.clear_main,e.current,e.callback,e.getsp,e.clear_idle};
    for(unsigned fault=0;fault<=18;++fault){
        Cpu c;auto& m=c.mmu.words;c.gpr[1]=sp;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        c.pc=e.thread.lr-4u;c.lr=c.pc;
        for(auto x:edges){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        m[W::Return]=e.return_word;m[W::CallbackPtr]=e.callback.pc;m[SramGuest+76]=1;
        if(fault==1)m[W::Thread+8]=1;
        if(fault==2)m[W::CallbackPtr]^=4;
        if(fault==3)c.msr|=0x8000;
        W witness(e);
        need(witness.begin(c)==!(fault>=1&&fault<=3));
        if(fault>=1&&fault<=3)continue;
        bool rejected=false;
        for(unsigned i=0;i<edges.size();++i){
            c.pc=edges[i].pc;c.lr=edges[i].lr;c.gpr[1]=i?frame:sp;c.inst_count+=100;
            bool bad=false;
            if(i==1){c.gpr[3]=W::Thread;m[0x800000d8u]=W::Thread;m[W::Thread+712]=0x00020001u;
                if(fault==4)m[W::Thread+712]=0;
                bad=fault==4;}
            if(i==2){m[0x800000d8u]=fault==5?W::Thread:0;bad=fault==5;}
            if(i==3){
                c.msr=fault==6?0x2002u:2u;c.ctr=e.callback.pc;c.gpr[12]=e.callback.pc;
                c.gpr[3]=0;c.gpr[4]=W::Thread;m[0x800000d4u]=W::Thread;
                m[0x800000c0u]=W::Thread&0x3fffffffu;
                m[W::Thread+772]=W::StackTop;m[W::Thread+776]=W::StackBottom;m[W::StackBottom]=0xdeadbabeu;
                if(fault==7)c.ctr^=4;
                if(fault==8)c.gpr[12]^=4;
                if(fault==9)m[W::StackBottom]=0;
                bad=fault>=6&&fault<=9;
            }
            if(i==4){m[0x800000e4u]=fault==10?0:W::Thread;bad=fault==10;}
            if(i==5){c.gpr[3]=fault==11?W::Thread:W::Idle;bad=fault==11;}
            need(witness.observe(c.pc,c)==!bad);if(bad){rejected=true;break;}
        }
        if(rejected)continue;
        c.pc=W::Return;c.lr=W::Return;c.gpr[1]=sp;c.inst_count+=100;
        m[0x800000dcu]=W::Thread;m[0x800000e0u]=W::Thread;m[frame]=sp;
        m[W::Thread+720]=16;m[W::Thread+724]=16;m[W::Thread+728]=0xffffffffu;
        if(fault==12)m[W::Thread+724]=15;
        if(fault==13)m[W::Thread+4]=1;
        if(fault==14)m[W::StackBottom+4]=1;
        if(fault==15)c.gpr[14]=1;
        if(fault==16)m[frame]=0;
        if(fault==17)m[0x800000dcu]=0;
        if(fault==18)c.lr^=4;
        need(witness.observe(c.pc,c)==(fault==0));if(!fault)need(witness.stage()==8);
    }
    std::cout<<"PASS: original-free default thread ABI, indirect callback, stack and context witness, 18 negative controls\n";
}
