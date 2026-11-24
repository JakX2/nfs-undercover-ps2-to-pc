#include "wii_full_hardware_witness.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
using R=FullStartResult;
struct Mmu {
    std::map<uint32_t,uint32_t> mem;
    uint32_t* get_ptr(uint32_t a){auto it=mem.find(a&~3u);return it==mem.end()?nullptr:&it->second;}
    uint32_t read32(uint32_t a){return mem.at(a);}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<double,32> fpr{},ps1{};std::array<uint32_t,8> gqr{};
    uint32_t pc=0,lr=0,msr=0,hid0=0x100,hid2=0x20,fpscr=0;uint64_t inst_count=0;bool is_running=true;
};
static void need(bool v,const char* s){if(!v)throw std::runtime_error(s);}
int main(){
    HardwareExpectations e{};e.ps_seed=0x80001000;e.scalar_seed=0x80001008;
    for(unsigned i=0;i<6;++i){auto& s=e.entries[i];s.pc=0x80004000+0x200*i;s.lr=s.pc+0x100;s.count=i==4?74:2;s.words.fill(0x60000000u);}
    for(unsigned fault=0;fault<9;++fault){
        Cpu c;c.gpr[1]=0x80010000;c.gqr.fill(1);c.mmu.mem[e.ps_seed]=0;c.mmu.mem[e.ps_seed+4]=0xc0200000u;c.mmu.mem[e.scalar_seed]=0x3ff00000u;c.mmu.mem[e.scalar_seed+4]=0x00012345u;
        for(const auto& s:e.entries)for(unsigned j=0;j<s.count;++j)c.mmu.mem[s.pc+j*4]=s.words[j];
        FullHardwareWitness w(e);need(w.begin(c),"begin");c.msr|=0x2000u;
        for(unsigned i=0;i<6;++i){
            const auto& s=e.entries[i];c.pc=s.pc;c.lr=s.lr;c.inst_count+=100;
            if(i==2)c.gpr[3]=c.hid2|0xa0000000u;
            if(i==3)c.hid2=c.gpr[3];
            if(i==4){c.hid0|=0x800u;c.gqr.fill(0);c.gpr[3]=0;}
            if(i==5){c.fpr.fill(std::bit_cast<double>(0x3ff0000000012345ull));c.ps1.fill(-2.5);c.fpscr=0x12345;}
            if(fault==1&&i==0)c.lr+=4;
            if(fault==2&&i==2)c.gpr[3]^=1;
            if(fault==3&&i==4)c.gqr[7]=1;
            if(fault==4&&i==5)c.ps1[31]=0;
            if(fault==5&&i==5)c.fpr[17]=0;
            if(fault==6&&i==5)c.fpscr^=1;
            if(fault==7&&i==4)c.mmu.mem[s.pc]^=1;
            if(fault==8&&i==5)c.inst_count-=30;
            auto r=w.observe(c.pc,c);
            if(r==R::Invalid){need(fault!=0,"valid path rejected");break;}
            if(i==5)need(!fault&&r==R::Complete,"invalid path accepted");
        }
        need(w.stage()==(fault==0?6u:fault==1?0u:fault==2?2u:fault==3||fault==7?4u:5u),"unexpected stage");
    }
    std::cout<<"PASS: hardware startup witness and eight negative controls\n";
}
