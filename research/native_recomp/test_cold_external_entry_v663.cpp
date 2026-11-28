#include "wii_cold_external_entry_v663.h"
#include <map>
#include <iostream>
using namespace undercover::wii;
using R=ColdExternalEntry;using W=IrqEnableWitness;
struct Mmu{
    std::map<uint32_t,uint8_t> mem;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t){return &byte;}
    uint8_t read8(uint32_t a){return mem[a];}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=v<<8|read8(a+i);return v;}
    void put(uint32_t a,uint32_t w){for(unsigned i=0;i<4;++i)mem[a+i]=uint8_t(w>>(24-8*i));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};
    uint32_t pc=W::Call,lr=W::Call,msr=0x32,ctr=5,xer=6,srr0=9,srr1=10,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;uint64_t inst_count=10;
};
static void need(bool v){if(!v)throw std::runtime_error("V663 synthetic assertion");}
int main(){
    constexpr uint64_t host_edge_ticks=1u-UNDERCOVER_WII_GUEST_ONLY_DISPATCH;
    ColdExternalExpectations e{{1,2,W::Entry+12,3,4},{},5,6};
    for(unsigned i=0;i<e.vector.size();++i)e.vector[i]=uint8_t(i);
    for(unsigned trial=0;trial<17;++trial){
        Cpu c;R route(e);auto& m=c.mmu;
        c.gpr[13]=0x8070e8e0u;
        for(unsigned i=0;i<32;++i)if(i!=13)c.gpr[i]=0x12340000u+i;
        for(unsigned i=0;i<e.vector.size();++i)m.mem[ExternalVector+i]=e.vector[i];
        m.put(W::Call,1);m.put(W::Entry,2);m.put(e.leaf.resume,3);
        m.put(R::Trampoline,5);m.put(R::Dispatcher,6);
        m.put(0x80000048,0x004e5090);m.put(0x800000d4,R::Thread);
        m.put(0x800000e4,R::Thread);m.put(0x800000c0,R::Thread&0x3fffffffu);
        m.put(0x80003010,R::Trampoline);m.put(0x80003090,0x80531b34u);
        if(trial==1)m.put(0x80003010,0);
        if(trial==2)m.mem[ExternalVector]^=1;
        uint32_t cause=trial==3?0:8,mask=8;
        if(trial==4)c.dispatch_saved_ctx=1;
        if(trial==5)c.msr|=0x8000;
        bool ok=route.begin(c,cause,mask);
        if(trial>=1&&trial<=5){need(!ok&&route.failure()==1);continue;}need(ok);
        need(!route.poll(c,cause,mask)&&!route.failure());
        c.pc=W::Entry;c.lr=W::Return;++c.inst_count;
        need(route.observe(c.pc,c,cause,mask)&&route.stage()==2);
        c.pc=e.leaf.resume;c.msr|=0x8000;c.inst_count+=3;
        if(trial==6)c.pc+=4;
        if(trial==7)cause|=16,mask|=16;
        const auto gp=c.gpr;const auto lr=c.lr,ctr=c.ctr,xer=c.xer,prior=c.msr;
        ok=route.poll(c,cause,mask);
        if(trial==6||trial==7){need(!ok&&route.failure());continue;}need(ok&&route.stage()==3);
        need(!route.poll(c,cause,mask)&&!route.failure());
        // Only legacy dispatch has a synthetic host tick; the negative
        // witness mutations must fail in either selected counter policy.
        c.inst_count+=(trial==12?1u-host_edge_ticks:host_edge_ticks);
        if(trial==13)++c.inst_count;
        if(trial==8)c.gpr[4]^=1;
        ok=route.observe(c.pc,c,cause,mask);
        if(trial==8||trial==12||trial==13){need(!ok&&route.failure()==6&&route.vector_refusal()==(trial==8?64u:2u));continue;}need(ok);
        c.pc=R::Trampoline;c.gpr[3]=4;c.gpr[4]=R::Thread;c.inst_count+=38;
        for(unsigned i=3;i<=5;++i)m.put(R::Thread+i*4,gp[i]);
        m.put(R::Thread+408,e.leaf.resume);m.put(R::Thread+412,prior&ExternalSrr1Mask);
        m.put(R::Thread+132,lr);m.put(R::Thread+136,ctr);m.put(R::Thread+140,xer);
        if(trial==9)m.put(R::Thread+408,0);
        ok=route.observe(c.pc,c,cause,mask);
        if(trial==9){need(!ok&&route.failure()==7);continue;}need(ok);
        c.pc=R::Dispatcher;c.inst_count+=30;
        for(unsigned i=6;i<32;++i)m.put(R::Thread+i*4,gp[i]);
        if(trial==10)m.put(R::Thread+31*4,0);
        if(trial==11)cause=0;
        if(trial==14)c.pc=R::Dispatcher+4;
        if(trial==15)c.gpr[4]^=4;
        if(trial==16)m.put(R::Thread+412,0);
        ok=route.observe(c.pc,c,cause,mask);
        if(trial==10){need(!ok&&route.failure()==8&&route.dispatcher_refusal()==256u&&route.saved_gpr_refusal()==0x80000000u);continue;}
        if(trial==11){need(!ok&&route.failure()==4);continue;}
        if(trial>=14){need(!ok&&route.failure()==8&&route.dispatcher_refusal()==(trial==14?1u:trial==15?16u:128u)&&!route.saved_gpr_refusal());continue;}
        need(ok&&route.stage()==6&&cause==8&&mask==8);
    }
    std::cout<<"V663_EXTERNAL synthetic=1 rejects=16 guest_only="<<UNDERCOVER_WII_GUEST_ONLY_DISPATCH
             <<" source_held=1 original_execution=0\n";
}
