#include "wii_saved_context_join_v921.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t Frame=0x80010000u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=0x80004000u,lr=0x80005000u,msr=0x8032u,ctr=5,xer=6,dispatch_saved_ctx=0;
    bool is_running=true,in_callback=false;uint64_t inst_count=100;
};
static void need(bool b){if(!b)throw std::runtime_error("context join assertion");}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned i=0;i<14;++i){
        Cpu c;ExternalReturnWitness w;SavedContextJoin j;
        for(unsigned k=0;k<32;++k)c.gpr[k]=0x12340000u+k;
        c.cr[0].lt=true;
        need(w.capture(c,8u,8u));
        for(unsigned k=0;k<32;++k)c.mmu.words[Frame+4*k]=c.gpr[k];
        c.mmu.words[Frame+128u]=0x80000000u;c.mmu.words[Frame+132u]=c.lr;
        c.mmu.words[Frame+136u]=c.ctr;c.mmu.words[Frame+140u]=c.xer;
        c.mmu.words[Frame+408u]=c.pc;c.mmu.words[Frame+412u]=c.msr&ExternalSrr1Mask;
        c.msr=0x32u;c.inst_count+=70;
        if(i==1)c.mmu.words[Frame]^=1u;
        if(i==2)c.mmu.words[Frame+412u]^=1u;
        if(i==3)c.msr|=0x8000u;
        bool ok=j.attach(c,w,Frame);
        if(i>=1&&i<=3){need(!ok&&j.failure()==1);++refused;continue;}
        need(ok&&j.stage()==1&&!j.captured());
        if(i==4){need(!j.attach(c,w,Frame));++refused;continue;}
        if(i!=5)c.inst_count+=100;
        if(i==6)c.mmu.words[Frame+4*31]^=1u;
        if(i==7)c.mmu.words[Frame+128u]^=1u;
        if(i==8)c.mmu.words.erase(Frame+140u);
        if(i==9)c.msr|=0x8000u;
        if(i==10)c.dispatch_saved_ctx=1;
        Cpu copy=c;
        ok=i==11?j.returned(copy,Frame):j.returned(c,i==12?Frame+4:Frame);
        if(i>=5&&i<=12){need(!ok&&j.failure()==2&&!j.captured());++refused;continue;}
        need(ok&&j.stage()==2&&j.captured()==&w&&j.context()==Frame&&w.stage()==1u);
        if(i==13){need(!j.returned(c,Frame)&&!j.captured());++refused;continue;}
        ++valid;
    }
    need(valid==1&&refused==13);
    std::cout<<"V921_CAPTURE_JOIN synthetic=1 valid=1 refused=13 original_execution=0\n";
}
