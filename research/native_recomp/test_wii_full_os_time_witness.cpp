#include "wii_full_os_time_witness.h"
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
struct Cpu {Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80520670u,lr=0x80004160u,msr=0;uint64_t inst_count=100,tb=0;bool is_running=true;uint64_t read_timebase() const{return tb;}};
static void need(bool ok){if(!ok)throw std::runtime_error("OS time witness");}
int main(){
    const OsTimeExpectations e{{OsTimeEdge{0x805450e8u,0x80520684u,1,2},OsTimeEdge{0x8052a844u,0x805206acu,3,4},OsTimeEdge{0x805265acu,0x8052a860u,5,6},OsTimeEdge{0x8052a824u,0x8052a868u,7,8},OsTimeEdge{0x805265d4u,0x8052a884u,9,10},OsTimeEdge{0x805265acu,0x805206b8u,11,6}}};
    for(unsigned mode=0;mode<4;++mode)for(unsigned fault=0;fault<14;++fault){
        Cpu c;constexpr uint32_t sp=0x80751cb0u,flag=0x8070dafcu,stamp=0x8070db30u,offset=0x800030d8u;
        const uint32_t msr=0x2000u|((mode&1u)?0x8000u:0u);
        const uint64_t lower=(mode&2u)?0xfffffffffffffffeull:0x12345678fffffffeull;
        const uint64_t off=0x100000007ull,upper=lower+8u,time=lower+3u+off;
        c.msr=msr;c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=0x8070e8e0u;
        for(unsigned i=20;i<32;++i)c.gpr[i]=0x200u+i;
        for(auto edge:e.edges){c.mmu.words[edge.pc]=edge.entry_word;c.mmu.words[edge.lr-4u]=edge.branch_word;}
        c.mmu.words[offset]=uint32_t(off>>32);c.mmu.words[offset+4]=uint32_t(off);
        if(fault==1)c.mmu.words[flag]=1;
        FullOsTimeWitness w(e);auto before=c.mmu.words;bool ok=w.begin(c);need(before==c.mmu.words);
        if(fault==1){need(!ok&&w.failure()==1);continue;}need(ok);
        bool failed=false;
        for(unsigned stage=0;stage<6;++stage){
            auto edge=e.edges[stage];c.pc=edge.pc;c.lr=edge.lr;c.inst_count+=10;
            if(stage==0){c.gpr[1]=sp-80;c.gpr[11]=sp;c.mmu.words[sp-80]=sp;c.mmu.words[sp+4]=0x80004160u;if(fault==2)c.mmu.words[sp+4]=0;if(fault==3)c.lr+=4;}
            if(stage==1){for(unsigned i=0;i<12;++i)c.mmu.words[sp-48+4*i]=c.gpr[20+i];c.mmu.words[flag]=1;if(fault==4)c.mmu.words[sp-48]=0;if(fault==5)c.mmu.words[flag]=0;}
            if(stage==2&&fault==6)c.gpr[13]++;
            if(stage==3){c.msr=msr&~0x8000u;c.tb=lower;if(fault==7)c.msr^=0x8000u;}
            if(stage==4){c.gpr[3]=unsigned((msr&0x8000u)!=0);c.tb=upper;if(fault==8)c.gpr[3]^=1;if(fault==9)c.tb=lower+1000001u;}
            if(stage==5){c.msr=msr;c.gpr[3]=uint32_t(time>>32);c.gpr[4]=uint32_t(time);if(fault==10)c.gpr[4]+=100;c.mmu.words[stamp]=c.gpr[3];c.mmu.words[stamp+4]=c.gpr[4];if(fault==11)c.mmu.words[stamp+4]^=1;if(fault==12)c.msr^=0x8000u;if(fault==13)c.mmu.words[offset+4]++;}
            before=c.mmu.words;ok=w.observe(c.pc,c);need(before==c.mmu.words);
            if(!ok){failed=true;break;}
        }
        need(failed==(fault!=0));if(!fault){need(w.stage()==6);need(!w.observe(c.pc,c));}
    }
    std::cout<<"PASS: four OS-time configurations, 52 negative controls and four duplicate stops\n";
}
