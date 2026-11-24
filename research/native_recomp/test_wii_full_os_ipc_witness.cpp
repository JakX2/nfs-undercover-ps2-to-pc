#include "wii_full_os_ipc_witness.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a<0x81800000u?&backing:nullptr;}
    uint32_t read32(uint32_t a){auto i=words.find(a);return i==words.end()?0u:i->second;}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80520818u,lr=pc,msr=0x2000u;uint64_t inst_count=100;bool is_running=true;};
static void need(bool b){if(!b)throw std::runtime_error("MEM2 IPC witness");}
int main(){
    const OsIpcExpectations e{{IpcEdge{0x80521d68u,0x80520890u,1,2},IpcEdge{0x80521d50u,0x805208a4u,3,4},IpcEdge{0x8052ae80u,0x805208a8u,5,6},IpcEdge{0x80520bf4u,0x805208acu,7,8}}};
    constexpr uint32_t sda=0x8070e8e0u;
    constexpr std::array<uint32_t,4> inputs{0x80003124u,0x80003128u,0x80003130u,0x80003134u},globals{sda-16396u,sda-3468u,sda-16336u,sda-3352u};
    constexpr std::array<uint32_t,6> guards{sda-16400u,sda-3472u,sda-16392u,sda-3464u,sda-16340u,sda-3348u};
    for(unsigned mode=0;mode<4;++mode)for(unsigned fault=0;fault<15;++fault){
        Cpu c;c.gpr[1]=0x80751c68u;c.gpr[2]=0x80715ee0u;c.gpr[13]=sda;
        const uint32_t low=mode==0?0x90000000u:mode==1?0x900007fcu:mode==2?0x90000800u:0x90010000u;
        const std::array<uint32_t,4> vals{low,0x93d00000u,0x93e00000u,0x94000000u};
        for(unsigned i=0;i<4;++i){c.mmu.words[inputs[i]]=vals[i];c.mmu.words[globals[i]]=10+i;}
        for(unsigned i=0;i<guards.size();++i)c.mmu.words[guards[i]]=50+i;
        for(auto edge:e.edges){c.mmu.words[edge.pc]=edge.entry_word;c.mmu.words[edge.lr-4]=edge.branch_word;}
        if(fault==1)c.mmu.words[inputs[0]]=0;
        if(fault==2)c.mmu.words[inputs[1]]=0x93f00000;
        if(fault==3)c.mmu.words[inputs[3]]=0x94000004;
        if(fault==4)c.mmu.words[inputs[2]]++;
        if(fault==5)c.msr|=0x8000u;
        FullOsIpcWitness w(e);auto before=c.mmu.words;bool ok=w.begin(c);need(before==c.mmu.words);
        if(fault>=1&&fault<=5){need(!ok);continue;}need(ok&&w.clamped()==(mode<2));
        const uint32_t selected=low<0x90000800u?0x90000800u:low;
        bool failed=false;
        for(unsigned stage=0;stage<4;++stage){
            c.pc=e.edges[stage].pc;c.lr=e.edges[stage].lr;c.inst_count+=10;
            if(stage==0){c.gpr[3]=selected;if(fault==6)c.gpr[3]+=4;if(fault==7)c.lr+=4;}
            if(stage==1){c.mmu.words[globals[0]]=selected;c.gpr[3]=vals[1];if(fault==8)c.mmu.words[globals[0]]+=4;if(fault==9)c.gpr[3]-=4;}
            if(stage==2){c.mmu.words[globals[1]]=vals[1];if(fault==10)c.mmu.words[inputs[2]]+=4;if(fault==11)c.mmu.words[guards[0]]++;}
            if(stage==3){c.mmu.words[globals[2]]=vals[2];c.mmu.words[globals[3]]=vals[3];if(fault==12)c.mmu.words[globals[3]]-=4;if(fault==13)c.gpr[1]-=8;if(fault==14)c.msr|=0x8000u;}
            before=c.mmu.words;ok=w.observe(c.pc,c);need(before==c.mmu.words);if(!ok){failed=true;break;}
        }
        need(failed==(fault!=0));if(!failed){need(w.stage()==4&&!w.active());need(!w.observe(c.pc,c));}
    }
    std::cout<<"PASS: four MEM2/IPC configurations, 56 negative controls and duplicate stops\n";
}
