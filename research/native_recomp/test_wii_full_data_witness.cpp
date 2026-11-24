#include "wii_full_data_witness.h"
#include <iostream>
#include <vector>
#include <stdexcept>
using namespace undercover::wii;
struct Mmu {
    std::vector<uint8_t> ram=std::vector<uint8_t>(0x200000u);
    uint8_t* get_ptr(uint32_t a){return a>=0x80000000u&&a-0x80000000u<ram.size()?ram.data()+a-0x80000000u:nullptr;}
    uint8_t read8(uint32_t a){return *get_ptr(a);}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cpu {Mmu mmu;std::array<uint32_t,32> gpr{};uint32_t pc=0x80004238u,lr=0x80004058u,msr=0x2000u;uint64_t inst_count=100u;bool is_running=true;};
static void need(bool v,const char* s){if(!v)throw std::runtime_error(s);}
int main(){
    DataExpectations e{};
    e.zero={DataRange{0x80010000u,950236u},DataRange{0x80110000u,13164u},DataRange{0x80120000u,56u}};
    for(unsigned i=0;i<3;++i){e.table[36+2*i]=e.zero[i].start;e.table[37+2*i]=e.zero[i].size;}
    e.set={0x8000443cu,0x800042bcu,0x1234u,0x5678u};e.fill={0x80004388u,0x80004454u,0x9abcu,0xdef0u};e.return_word=0x12345678u;
    for(unsigned fault=0;fault<10;++fault){
        Cpu c;constexpr uint32_t sp=0x801f0000u;c.gpr[1]=sp;for(unsigned i=13;i<32;++i)c.gpr[i]=i*17;
        for(unsigned i=0;i<44;++i)c.mmu.write32(0x80006420u+i*4,e.table[i]);
        for(auto range:e.zero){std::fill_n(c.mmu.get_ptr(range.start),range.size,0x55u);*c.mmu.get_ptr(range.start-1)=0x12;*c.mmu.get_ptr(range.start+range.size)=0x34;}
        for(auto edge:{e.set,e.fill}){c.mmu.write32(edge.pc,edge.entry_word);c.mmu.write32(edge.lr-4,edge.branch_word);}
        c.mmu.write32(0x80004058u,e.return_word);c.mmu.write32(sp,0xffffffffu);c.mmu.write32(sp+4,0x80004058u);
        FullDataWitness w(e);
        if(fault==1)c.mmu.write32(0x80006420u,1u);
        const bool begun=w.begin(c);if(fault==1){need(!begun,"wrong table");continue;}need(begun&&w.before_nonzero()==963456u,"begin");
        bool failed=false;
        for(unsigned i=0;i<6;++i){
            auto a=i%2?e.fill:e.set;auto b=e.zero[i/2];c.pc=a.pc;c.lr=a.lr;c.inst_count+=10;c.gpr[3]=b.start;c.gpr[4]=0;c.gpr[5]=b.size;
            if(fault==2&&i==0)c.gpr[5]--;
            if(fault==3&&i==1)c.lr+=4;
            if(!w.observe(c.pc,c)){failed=true;break;}
            if(i%2){std::fill_n(c.mmu.get_ptr(b.start),b.size,0);if(fault==4&&i==1)*c.mmu.get_ptr(b.start)=1;}
        }
        if(fault>=2&&fault<=4){need(failed,"bad helper accepted");continue;}need(!failed&&w.stage()==6,"helpers");
        c.pc=c.lr=0x80004058u;c.inst_count+=100;
        if(fault==5)c.gpr[31]++;
        if(fault==6)c.mmu.write32(sp+4,0u);
        if(fault==7)*c.mmu.get_ptr(e.zero[2].start+e.zero[2].size)=0;
        if(fault==8)*c.mmu.get_ptr(e.zero[2].start)=1;
        if(fault==9)c.pc+=4;
        need(w.finish(c)==(fault==0),"finish classification");
    }
    std::cout<<"PASS: complete data witness, 963456 BSS bytes, six call edges and nine negative controls\n";
}
