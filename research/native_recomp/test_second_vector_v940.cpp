#include "wii_second_vector_v939.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t V=ExternalVector,T=0x80006000u,D=0x80005000u,C=0x80010000u,H=0x80004000u,Other=0x100u,Mask=8u;
constexpr uint32_t Nop=0x60000000u,Rfi=0x4c000064u;
constexpr uint32_t branch(uint32_t a,uint32_t b){return 0x48000000u|((b-a)&0x03fffffcu);}
constexpr std::array<uint32_t,2> Vec{Nop,Rfi},Tramp{Nop,branch(T+4,D)};
constexpr std::array<uint8_t,8> Image{0x60,0,0,0,0x4c,0,0,0x64};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t p){return words.count(p&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t p){return words.at(p);}
    uint8_t read8(uint32_t p){return uint8_t(read32(p&~3u)>>(24u-8u*(p&3u)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=0x80007000u,msr=0x8032u,ctr=17,xer=0x80000000u,srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("V940 second vector assertion");}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned i=0;i<16;++i){
        Cpu c;PendingExternalReentry reentry;SecondVectorWitness w({T,D,C,Nop,Vec,Tramp});
        c.mmu.words={{V,Vec[0]},{V+4,Vec[1]},{T,Tramp[0]},{T+4,Tramp[1]},{D,Nop}};
        for(unsigned k=0;k<32;++k)c.gpr[k]=k*17u+3u;
        const auto gp=c.gpr;const uint32_t lr=c.lr,ctr=c.ctr,xer=c.xer;
        for(unsigned k=0;k<32;++k)c.mmu.words[C+4*k]=0;
        for(unsigned off:{128u,132u,136u,140u,408u,412u})c.mmu.words[C+off]=0;
        need(reentry.enter(c,Other|Mask,Mask,Image,true,true)&&reentry.outer_poll(c,Other|Mask,Mask,true));
        ++c.inst_count;need(reentry.vector_entry(c,V,Other|Mask,Mask,true));
        if(i==1)c.mmu.words[T]^=1u;
        bool ok=w.begin(c,reentry,Other|Mask,Mask,i!=2);
        if(i==1||i==2){need(!ok&&w.failure()==1);++refused;continue;}need(ok);
        if(i!=3)++c.inst_count;
        if(i==4)c.gqr[2]^=1u;
        ok=w.before(c,i==5?V+4:V,Vec[0],Other|Mask,Mask,true);
        if(i>=3&&i<=5){need(!ok&&w.failure()==2);++refused;continue;}need(ok);
        // Model the effect of the synthetic vector before its synthetic RFI.
        // No original vector or host-generated guest instruction execution.
        c.srr0=i==6?D:T;c.srr1=i==7?0x8032u:0x32u;++c.inst_count;
        for(unsigned k=3;k<=5;++k)c.mmu.words[C+4*k]=gp[k];
        c.mmu.words[C+132]=lr;c.mmu.words[C+136]=ctr;c.mmu.words[C+140]=xer;
        c.mmu.words[C+408]=H;c.mmu.words[C+412]=0x8032u;
        ok=w.before(c,V+4,Rfi,Other|Mask,Mask,true);
        if(i==6||i==7){need(!ok&&w.failure()==3);++refused;continue;}need(ok);
        c.pc=T;c.msr=c.srr1;c.gpr[3]=4;c.gpr[4]=C;
        if(i==8)c.pc=D;
        if(i==9)c.msr^=1u;
        ok=w.poll(c,Other|Mask,Mask,true);
        if(i==8||i==9){need(!ok&&w.failure()==4);++refused;continue;}need(ok);
        if(i!=10)++c.inst_count;
        if(i==11)c.mmu.words[C+12]^=1u;
        ok=w.entry(c,T,Other|Mask,Mask,true);
        if(i==10||i==11){need(!ok&&w.failure()==(i==10?5u:6u));++refused;continue;}need(ok&&w.stage()==2);
        ++c.inst_count;need(w.before(c,T,Tramp[0],Other|Mask,Mask,true));
        ++c.inst_count;need(w.before(c,T+4,Tramp[1],Other|Mask,Mask,true));
        for(unsigned k=0;k<32;++k)c.mmu.words[C+4*k]=gp[k];
        c.pc=D;
        need(w.poll(c,Other|Mask,Mask,true));
        if(i!=14)++c.inst_count;
        if(i==12)c.mmu.words[C+124]^=1u;
        if(i==13)c.mmu.words[C+128]^=1u;
        ok=w.entry(c,D,Other|Mask,Mask,i!=15);
        if(i>=12){need(!ok&&w.failure()==(i<=13?6u:5u));++refused;continue;}
        need(ok&&w.stage()==3&&w.vector_visits()==2&&w.trampoline_visits()==2&&!w.gpr_mask()&&!w.special_mask());++valid;
    }
    need(valid==1&&refused==15);
    std::cout<<"V940_SECOND_VECTOR_WITNESS synthetic=1 valid=1 refused=15 original_execution=0\n";
}
