#include "wii_second_si_dispatch_v944.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
using R=SiDispatchWitness;
constexpr uint32_t Resume=0x80004000u,Other=0x100u,Mask=8u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=0x80005000u,msr=0x8032u,ctr=17,xer=0x80000000u,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;uint64_t inst_count=100;
};
static void need(bool b){if(!b)throw std::runtime_error("V944 dispatcher assertion");}
int main(){
    const SiDispatchExpectations e{{{{0x80010000,0x80011004,1,2},
        {0x80012000,0x80011008,3,4},{0x80013000,0x80012004,5,6},
        {0x80014000,0x80012008,7,8}}},0x8001100c,0x4e800421,9,10};
    unsigned valid=0,refused=0;
    for(unsigned i=0;i<17;++i){
        Cpu c;ExternalReturnWitness capture;SecondSiDispatchWitness w(e);auto& m=c.mmu.words;
        for(unsigned k=0;k<32;++k)c.gpr[k]=k*17u+3u;
        need(capture.capture(c,Other|Mask,Mask));
        for(unsigned k=0;k<32;++k)m[R::Thread+4u*k]=c.gpr[k];
        m[R::Thread+128]=0;m[R::Thread+132]=c.lr;m[R::Thread+136]=c.ctr;m[R::Thread+140]=c.xer;
        m[R::Thread+408]=Resume;m[R::Thread+412]=c.msr;
        c.msr=0x32u;c.pc=R::Dispatcher;c.gpr[3]=4;c.gpr[4]=R::Thread;c.inst_count+=50u;
        m[c.pc]=10;m[0x80003090u]=R::Handler;m[0x800000d4u]=m[0x800000e4u]=R::Thread;
        m[e.indirect_pc]=e.indirect_word;m[R::Handler]=e.handler_word;
        for(auto x:e.edges){m[x.pc]=x.entry_word;m[x.lr-4u]=x.branch_word;}
        if(i==1)c.gpr[4]=0;
        if(i==2)m[R::Thread+124]^=1u;
        bool ok=w.begin(c,capture,i==3?Mask:Other|Mask,Mask,i!=4);
        if(i>=1&&i<=4){need(!ok&&w.failure()==1u);++refused;continue;}need(ok);
        if(i==5)c.msr|=0x8000u;
        ok=w.poll(c,Other|Mask,Mask,true);
        if(i==5){need(!ok&&w.failure()==2u);++refused;continue;}need(ok);
        if(i!=6)w.record(false,0xcc003000u,32,Other|Mask,false);
        if(i!=7)w.record(false,0xcc003004u,32,Mask,false);
        if(i==8)w.record(true,0xcc003000u,32,Other|Mask,false);
        if(i==9)w.record(false,0xcc003004u,16,Mask,false);
        if(i==10)w.record(false,0xcc003004u,32,Mask,true);
        if(i==11)w.record(false,0xcc003004u,32,0,false);
        for(unsigned k=0;k<e.edges.size();++k){
            const auto x=e.edges[k];c.pc=x.pc;c.lr=x.lr;++c.inst_count;
            if(i==12&&k==1)c.lr+=4;
            if(i==13&&k==2)m[R::Thread+0x80]^=1u;
            ok=w.observe(c,c.pc,Other|Mask,Mask,true);
            if(!ok)break;
        }
        if(i>=8&&i<=13){need(!ok&&w.failure()==(i==12?4u:3u));++refused;continue;}need(ok);
        c.pc=R::Handler;c.ctr=R::Handler;c.gpr[3]=20;c.gpr[4]=R::Thread;c.lr=e.indirect_pc+4u;++c.inst_count;
        if(i==14)c.gpr[3]=27;
        if(i==15)m[0x80003090u]^=4u;
        ok=w.observe(c,c.pc,Other|Mask,Mask,i!=16);
        if(i){need(!ok&&w.failure()==(i==15||i==16?3u:5u));++refused;continue;}
        need(ok&&w.stage()==6u);++valid;
    }
    need(valid==1&&refused==16);
    std::cout<<"V944_SECOND_DISPATCH synthetic=1 valid=1 refused=16 pi_reads=1 captured_context=1 original_execution=0\n";
}
