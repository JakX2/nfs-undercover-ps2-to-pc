#include "wii_full_os_entry_witness.h"
#include <array>
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu {
    std::map<uint32_t,uint32_t> words;
    uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&byte:nullptr;}
    uint32_t read32(uint32_t a){auto i=words.find(a);return i==words.end()?0u:i->second;}
};
struct Cpu {Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80004058u,lr=pc;uint64_t inst_count=100;bool is_running=true;};
static void need(bool ok){if(!ok)throw std::runtime_error("OS entry witness");}
int main(){
    constexpr OsEntryExpectations e{1,2,3,4};
    for(unsigned mode=0;mode<4;++mode)for(unsigned fault=0;fault<12;++fault){
        Cpu c;c.gpr[1]=0x80751cb0u;c.gpr[2]=0x80715ee0u;c.gpr[13]=0x8070e8e0u;
        c.mmu.words={{0x80000034u,mode&1u?0x81700000u:0u},{0x800000f4u,mode&2u?0x81701000u:0u},{0x80004158u,e.db_branch},{0x804e5020u,e.db_entry},{0x8000415cu,e.os_branch},{0x80520670u,e.os_entry},{0x80000044u,99u}};
        FullOsEntryWitness w(e);if(fault==1)c.lr+=4;
        const auto before=c.mmu.words;const bool b=w.begin(c);need(c.mmu.words==before);
        if(fault==1){need(!b&&w.failure()==1);continue;}
        need(b&&w.arena_hi_nonzero()==bool(mode&1u)&&w.boot_info_nonzero()==bool(mode&2u));
        c.pc=0x804e5020u;c.lr=0x8000415cu;c.inst_count+=10;
        if(fault==2)c.inst_count-=10;
        if(fault==3)c.pc+=4;
        if(fault==4)c.lr+=4;
        if(fault==5)c.gpr[13]++;
        if(fault==6)c.mmu.words[0x80004158u]++;
        const bool d=w.observe(c.pc,c);
        if(fault>=2&&fault<=6){need(!d&&w.failure()!=0);continue;}need(d&&w.stage()==2);
        c.mmu.words[0x80000044u]=0;c.mmu.words[0x80000048u]=0x004e5090u;c.mmu.words[0x8070d8a0u]=0x80000040u;c.mmu.words[0x8070d8a4u]=1;
        c.pc=0x80520670u;c.lr=0x80004160u;c.inst_count+=10;
        if(fault==7)c.mmu.words[0x80000044u]=1;
        if(fault==8)c.mmu.words[0x80000048u]=0;
        if(fault==9)c.mmu.words[0x8070d8a0u]=0;
        if(fault==10)c.mmu.words[0x8070d8a4u]=0;
        if(fault==11)c.mmu.words[0x80520670u]++;
        const auto snapshot=c.mmu.words;need(w.observe(c.pc,c)==(fault==0));need(c.mmu.words==snapshot);
        if(!fault){need(w.stage()==3&&!w.observe(c.pc,c));}
    }
    std::cout<<"PASS: four boot-metadata combinations, 44 negative controls, four duplicate-stop controls\n";
}
