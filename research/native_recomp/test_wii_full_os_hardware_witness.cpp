#include "wii_full_os_hardware_witness.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu {
    std::map<uint32_t,uint8_t> bytes;uint8_t backing=0;
    uint8_t* get_ptr(uint32_t a){return ((a>=0x80000000u&&a<0x81800000u)||(a>=0x90000000u&&a<0x94000000u))?&backing:nullptr;}
    uint8_t read8(uint32_t a){auto i=bytes.find(a);return i==bytes.end()?0:i->second;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(24-8*i));}
};
struct Cpu {Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,4> pmc{1,2,3,4};uint32_t pc=0x805265acu,lr=0x805206b8u,msr=0x2000u,hid0=0xc800u,hid2=0xa0000000u,l2cr=0x80000000u,fpscr=0x20u,hid4=0,mmcr0=5,mmcr1=6;uint64_t inst_count=100;bool is_running=true;};
static void need(bool b){if(!b)throw std::runtime_error("OS hardware witness");}
int main(){
    OsHardwareExpectations e{{},0x1234u,0x5678u,0xabcdefu};
    constexpr uint32_t dest=0x806f4f00u,ptr_word=0x800030f0u,stamp=0x8070db30u,sp=0x80751c60u;
    for(unsigned i=0;i<12;++i)e.edges[i]={0x80540000u+i*0x10u,0x80550004u+i*4u,0x100u+i,0x200u+i};
    for(unsigned mode=0;mode<4;++mode)for(unsigned fault=0;fault<13;++fault){
        Cpu c;const uint32_t ptr=mode==0?0u:mode==1?0x7fffffffu:mode==2?0x80030000u:0x90010000u;
        const bool copied=ptr>=0x80000000u;c.msr|=(mode&1u)?0x8000u:0u;
        c.gpr[1]=sp;c.gpr[2]=0x80715ee0u;c.gpr[13]=0x8070e8e0u;
        c.mmu.write32(ptr_word,ptr);c.mmu.write32(stamp,123);c.mmu.write32(stamp+4,456);
        for(unsigned i=0;i<30;++i)c.mmu.bytes[dest-1+i]=uint8_t(i+10);
        if(copied)for(unsigned i=0;i<28;++i)c.mmu.bytes[ptr+i]=uint8_t(100+i);
        for(auto edge:e.edges){c.mmu.write32(edge.pc,edge.entry_word);c.mmu.write32(edge.lr-4,edge.branch_word);}
        c.mmu.write32(0x80004338u,e.copy_entry);c.mmu.write32(0x80523b30u,e.copy_branch);c.mmu.write32(0x80520700u,e.stop_word);
        FullOsHardwareWitness w(e);auto old=c.mmu.bytes;need(w.begin(c)&&w.copied()==copied&&old==c.mmu.bytes);bool failed=false;
        for(unsigned stage=0;stage<13;++stage){
            c.inst_count+=10;c.msr&=~0x8000u;
            c.pc=stage<12?e.edges[stage].pc:0x80520700u;c.lr=stage<12?e.edges[stage].lr:c.pc;
            if(stage==0){c.gpr[3]=dest;if(fault==1)c.gpr[3]++;if(fault==2)c.msr|=0x8000u;}
            if(stage==1){
                if(copied&&fault!=3){auto pc=c.pc,lr=c.lr;c.pc=0x80004338u;c.lr=0x805206c0u;c.gpr[3]=dest;c.gpr[4]=ptr;c.gpr[5]=28;if(fault==4)c.gpr[5]--;
                    old=c.mmu.bytes;bool ok=w.observe(c.pc,c);need(old==c.mmu.bytes);if(!ok){failed=true;break;}c.pc=pc;c.lr=lr;c.inst_count++;}
                for(unsigned i=0;i<28;++i)c.mmu.bytes[dest+i]=copied?c.mmu.read8(ptr+i):(i<4?0:c.mmu.read8(dest+i));
                if(fault==5)c.mmu.bytes[dest+28]^=1;
                if(fault==6)c.mmu.bytes[dest+3]^=1;
            }
            if(stage>=1&&stage<=6){c.gpr[3]=0;if(stage==2&&fault!=7)c.mmcr0=0;if(stage==3)c.mmcr1=0;if(stage>=4)c.pmc[stage-4]=0;}
            if(stage==7){c.pmc[3]=0;c.gpr[3]=0x83900000u;if(fault==8)c.gpr[3]++;}
            if(stage==8){c.hid4=0x83900000u;if(fault==9)c.hid4=0;}
            if(stage==10){c.gpr[3]=c.hid0|0x200u;if(fault==10)c.gpr[3]^=1;}
            if(stage==11)c.hid0|=0x200u;
            if(stage==12){c.fpscr|=4u;if(fault==11)c.fpscr^=4u;if(fault==12)c.gpr[1]-=8;}
            old=c.mmu.bytes;bool ok=w.observe(c.pc,c);need(old==c.mmu.bytes);if(!ok){failed=true;break;}
        }
        const bool bad=fault!=0&&((fault!=3&&fault!=4)||copied);need(failed==bad);
        if(!bad){need(w.stage()==13&&!w.active());need(!w.observe(c.pc,c));}
    }
    std::cout<<"PASS: four exec-parameter modes, 44 negative controls, eight successful paths and duplicate stops\n";
}
