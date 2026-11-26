#include "wii_handler_suffix_guard_v868.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,SP=0x80010000u,Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t bc(unsigned bo,unsigned bi,int disp){return 0x40000000u|(bo<<21)|(bi<<16)|(uint32_t(disp)&0xfffcu);}
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    struct Mmu{
        std::map<uint32_t,uint8_t> data;
        const uint8_t* get_ptr(uint32_t a)const{auto i=data.find(a);return i==data.end()?nullptr:&i->second;}
        uint8_t read8(uint32_t a)const{return data.at(a);}
        uint32_t read32(uint32_t a)const{uint32_t w=0;for(unsigned i=0;i<4;++i)w=(w<<8)|read8(a+i);return w;}
        void put(uint32_t a,uint32_t w){for(unsigned i=0;i<4;++i)data[a+i]=uint8_t(w>>(24-8*i));}
    }mmu;
    std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,ctr=2;uint64_t inst_count=20;
};
static void need(bool v){if(!v)throw std::runtime_error("V1005 strict suffix");}
int main(){
    unsigned valid=0,bad=0;
    for(unsigned f=0;f<12;++f){
        Cpu c;c.gpr[1]=SP;c.cr[0].eq=f!=1;c.ctr=f==2?1u:2u;
        std::array<HandlerSuffixLabel,6> rows{{{H,Nop,0,0},{H+4,bc(12,2,8),0,0},{H+8,Nop,0,0},
            {H+12,Nop,0,0},{H+16,bc(16,0,-4),0,0},{H+20,Blr,12,1}}};
        if(f==4)rows[1].word=bc(12,2,32);
        if(f==5)rows[1].word|=2u;
        if(f==10)rows[1].word=0x44000002u;
        if(f==11)rows[1].word=0x48000001u;
        for(auto x:rows)c.mmu.put(x.pc,x.word);
        HandlerSuffixGuard g;need(g.start(c,rows,H,64u,true));
        auto step=[&](unsigned i){auto x=rows[i];bool ok=g.before(c,x.pc,x.word,x.ordinal,x.kind);++c.inst_count;return ok;};
        need(step(0));
        if(f==3){need(!step(2));++bad;continue;}
        if(f==9)c.gpr[1]+=4;
        bool ok=step(1);
        if(f==4||f==5||f>=9){need(!ok);++bad;continue;}need(ok);
        if(f==6){need(!step(2));++bad;continue;}
        if(f==1)need(step(2));
        need(step(3)&&step(4));--c.ctr;
        if(f==7){need(!step(5));++bad;continue;}
        if(f!=2){need(step(3)&&step(4));--c.ctr;}
        need(step(5));
        if(f==8){need(!step(5));++bad;continue;}
        ++valid;
    }
    need(valid==3&&bad==9);
    std::cout<<"V1005_STRICT_HANDLER_SUFFIX valid=3 refused=9 original_execution=0\n";
}
