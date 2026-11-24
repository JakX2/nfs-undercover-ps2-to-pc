#include "wii_irq_enable_witness_v615.h"
#include <iostream>
#include <map>
#include <source_location>
#include <stdexcept>
using W=undercover::wii::IrqEnableWitness;
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw std::runtime_error("V615 line "+std::to_string(l.line()));
}
struct Mmu{
    std::map<uint32_t,uint32_t> m;uint8_t dummy=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&dummy:nullptr;}
    uint32_t read32(uint32_t a){return m[a];}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0,lr=0,msr=0x32,ctr=0x123,srr0=0x456,srr1=0x789,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true;
};
int main(){
    constexpr uint32_t resume=W::Entry+12;
    for(unsigned fault=0;fault<=15;++fault){
        undercover::wii::IrqEnableExpectations e{1,2,resume,3,4};W w(e);Cpu c;
        c.pc=c.lr=W::Call;c.gpr[1]=0x80751c60;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        auto& m=c.mmu.m;m[W::Call]=1;m[W::Entry]=2;m[resume]=3;m[W::Return]=4;m[0x80000048]=0x004e5090;
        uint32_t cause=0x10,mask=0x40;
        if(fault==1)c.msr|=0x8000;
        if(fault==2)cause|=mask;
        if(fault==3)m[0x80000048]=0;
        need(w.begin(c,cause,mask)==(fault<1||fault>3));if(fault>=1&&fault<=3){need(w.entry_refusal()==(fault==1?8u:fault==2?32u:128u));continue;}need(w.entry_refusal()==0);
        c.pc=W::Entry;c.lr=W::Return;c.inst_count++;
        if(fault==4)c.lr+=4;
        if(fault==5)m[W::Entry]=0;
        if(fault==6)c.gpr[1]-=16;
        need(w.observe(c.pc,c,cause,mask)==(fault<4||fault>6));if(fault>=4&&fault<=6)continue;
        c.pc=resume;c.inst_count+=3;c.msr|=0x8000;
        if(fault==7)c.msr&=~0x8000;
        if(fault==8)c.inst_count--;
        if(fault==9)c.dispatch_saved_ctx=0x80003000;
        if(fault==10)cause|=mask;
        if(fault==11)c.srr1^=1;
        need(w.observe(c.pc,c,cause,mask)==(fault<7||fault>11));if(fault>=7&&fault<=11)continue;
        c.pc=c.lr=W::Return;c.inst_count+=2;c.gpr[3]=0;
        if(fault==12)c.gpr[3]=1;
        if(fault==13)c.gpr[31]^=1;
        if(fault==14)c.inst_count++;
        if(fault==15)m[W::Return]=0;
        need(w.observe(c.pc,c,cause,mask)==(fault==0));
        if(!fault){need(w.stage()==4&&!w.failure());need(!w.observe(c.pc,c,cause,mask));}
        else need(w.failure()!=0);
    }
    std::cout<<"V615_IRQ_WITNESS stages=4 refusal=15 exact_ticks=5 actual_irq=0 boot_verified=0\n";
}
