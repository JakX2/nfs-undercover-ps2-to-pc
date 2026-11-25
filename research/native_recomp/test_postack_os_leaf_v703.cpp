#include "wii_postack_os_leaf_v703.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t Site=0x80004000u,Root=0x80005000u,Branch=0x48001001u,
    Nop=0x60000000u,Blr=0x4e800020u,Mtmsr=0x7c000124u;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t p){return p>=Root&&p<Root+32?&b:nullptr;}
    uint32_t read32(uint32_t p){return words.at(p);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=Site,lr=0,msr=0x32,ctr=0,srr0=0x80009000,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool v){if(!v)throw std::runtime_error("V703 leaf assertion");}
int main(){
    for(unsigned trial=0;trial<15;++trial){
        Cpu c;c.gpr[0]=c.msr;const bool time=trial==1;
        const unsigned kind=time?2u:trial==2||trial==3?3u:1u;
        if(trial==3)c.gpr[3]=1;
        PostAckOsLeaf leaf({Site,Root,Root+12,Branch,kind});
        auto ok=leaf.start(c,Site,trial==4?Branch+4:Branch);
        if(trial==3||trial==4){need(!ok&&leaf.failure()==1);continue;}need(ok);
        c.pc=Root;c.lr=trial==5?Site:Site+4;
        ok=leaf.entry(Root,c);
        if(trial==5){need(!ok&&leaf.failure()==2);continue;}need(ok);
        c.mmu.words[Root]=Nop;c.mmu.words[Root+4]=time?Nop:Mtmsr;c.mmu.words[Root+8]=Blr;
        ++c.inst_count;if(trial==6)++c.inst_count;
        ok=leaf.before(c,Root,Nop);
        if(trial==6){need(!ok&&leaf.failure()==3);continue;}need(ok);
        ++c.inst_count;
        if(trial==7)c.gpr[0]|=0x8000;
        if(trial==8)c.mmu.words[Root+4]^=1;
        if(trial==9)c.mmu.words[Root+4]=0x48000101u;
        ok=leaf.before(c,Root+4,trial==9?0x48000101u:time?Nop:Mtmsr);
        if(trial>=7&&trial<=9){need(!ok&&leaf.failure()==(trial==7?5u:trial==8?3u:6u));continue;}need(ok);
        if(trial==11){need(!leaf.poll(c)&&leaf.failure()==5);continue;}
        if(trial==12)c.msr|=0x8000;
        ++c.inst_count;if(trial==10)++c.inst_count;
        ok=leaf.before(c,Root+8,Blr);
        if(trial==10||trial==12){need(!ok&&leaf.failure()==3);continue;}need(ok);
        c.pc=Site+4;++c.inst_count;if(trial==13)c.gpr[14]^=1;if(trial==14)c.srr0^=4;
        ok=leaf.returned(c,c.pc);
        if(trial>=13){need(!ok&&leaf.failure()==4);continue;}
        need(ok&&leaf.stage()==4&&leaf.visits()==3&&leaf.msr_writes()==(time?0u:1u));
    }
    std::cout<<"V703_OS_LEAF synthetic=1 cases=15 valid=3 rejects=12 original_execution=0\n";
    constexpr uint32_t Back=0x4082fffcu;
    for(unsigned trial=0;trial<8;++trial){
        Cpu c;PostAckOsLeaf leaf({Site,Root,Root+12,Branch,trial==7?1u:2u});
        need(leaf.start(c,Site,Branch));c.pc=Root;c.lr=Site+4;need(leaf.entry(Root,c));
        c.mmu.words={{Root,Nop},{Root+4,Back},{Root+8,Blr}};
        ++c.inst_count;need(leaf.before(c,Root,Nop));++c.inst_count;
        const bool ok=leaf.before(c,Root+4,Back);
        if(trial==7){need(!ok&&leaf.failure()==6);continue;}need(ok);
        c.pc=Root+4;
        if(trial==2){++c.inst_count;need(!leaf.before(c,Root+8,Blr)&&leaf.failure()==3);continue;}
        if(trial==3)c.pc=Root;
        if(trial==4)++c.inst_count;
        if(trial==5)c.msr|=0x8000;
        const bool polled=leaf.poll(c);
        if(trial>=3&&trial<=5){need(!polled&&leaf.failure()==5);continue;}need(polled);
        if(trial==6){need(!leaf.poll(c)&&leaf.failure()==5);continue;}
        if(trial==1){
            ++c.inst_count;need(leaf.before(c,Root,Nop));
            ++c.inst_count;need(leaf.before(c,Root+4,Back));need(leaf.poll(c));
        }
        ++c.inst_count;need(leaf.before(c,Root+8,Blr));
        c.pc=Site+4;++c.inst_count;need(leaf.returned(c,c.pc)&&leaf.polls()==trial+1);
    }
    std::cout<<"V717_LOOP_POLL synthetic=1 cases=8 valid=2 rejects=6 original_execution=0\n";
}
