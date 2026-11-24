#include "wii_si_dispatch_v667.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
using R=SiDispatchWitness;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t){return &byte;}
    uint32_t read32(uint32_t a){return words[a];}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=R::Dispatcher,lr=0,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;uint64_t inst_count=100;
};
static void need(bool v){if(!v)throw std::runtime_error("V667 synthetic assertion");}
int main(){
    const SiDispatchExpectations e{{{{0x8052a824,0x80526c84,1,2},
        {0x805293f8,0x80526c98,3,4},{0x805265ac,0x80529404,5,6},
        {0x805265d4,0x80529424,7,8}}},0x80526ca8,0x4e800421,9,10};
    for(unsigned trial=0;trial<13;++trial){
        si_dispatch_pi_reads=SiDispatchPiReads{};Cpu c;R r(e);auto& m=c.mmu.words;
        c.gpr[3]=4;c.gpr[4]=R::Thread;
        m[c.pc]=10;m[0x80003090]=R::Handler;m[0x800000d4]=m[0x800000e4]=R::Thread;
        m[R::Thread+408]=0x805265cc;m[R::Thread+412]=0x8032;
        m[e.indirect_pc]=e.indirect_word;m[R::Handler]=e.handler_word;
        for(auto x:e.edges){m[x.pc]=x.entry_word;m[x.lr-4]=x.branch_word;}
        uint32_t cause=8,mask=8,control=0xe0010300,status=0x08000000;
        if(trial==1)c.gpr[4]=0;
        if(trial==2)control^=0x80000000;
        if(trial==3)mask=0;
        bool ok=r.begin(c,cause,mask,control,status);
        if(trial>=1&&trial<=3){need(!ok&&r.failure()==1);continue;}need(ok);
        if(trial==4)c.msr|=0x8000;
        ok=r.poll(c,cause,mask);
        if(trial==4){need(!ok&&r.failure()==2);continue;}need(ok);
        if(trial!=5)si_dispatch_pi_reads.record(false,0xcc003000,32,cause,false);
        if(trial!=6)si_dispatch_pi_reads.record(false,0xcc003004,32,mask,false);
        if(trial==7)si_dispatch_pi_reads.record(true,0xcc003000,32,8,false);
        if(trial==8)si_dispatch_pi_reads.record(false,0xcc003004,32,0,false);
        if(trial==9)si_dispatch_pi_reads.record(false,0xcc003000,16,8,false);
        for(unsigned i=0;i<e.edges.size();++i){
            auto x=e.edges[i];c.pc=x.pc;c.lr=x.lr;++c.inst_count;
            if(trial==10&&i==1)c.lr+=4;
            ok=r.observe(c.pc,c,cause,mask,control,status);
            if(!ok)break;
        }
        if(trial>=7&&trial<=10){need(!ok&&r.failure());continue;}need(ok);
        c.pc=R::Handler;c.ctr=R::Handler;c.gpr[3]=20;c.gpr[4]=R::Thread;
        c.lr=e.indirect_pc+4;++c.inst_count;
        if(trial==11)c.gpr[3]=27;
        if(trial==12)m[R::Thread+408]^=4;
        ok=r.observe(c.pc,c,cause,mask,control,status);
        if(trial){need(!ok&&r.failure()==5);continue;}
        need(ok&&r.stage()==6&&cause==8&&mask==8);
    }
    std::cout<<"V667_SI_DISPATCH synthetic=1 rejects=12 pi_reads=1 no_ack=1 original_execution=0\n";
}
