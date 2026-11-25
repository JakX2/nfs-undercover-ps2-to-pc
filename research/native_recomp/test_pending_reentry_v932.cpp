#include "wii_pending_external_reentry_v932.h"
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,Other=0x100u,Mask=8u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t p){return words.count(p&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t p){return words.at(p);}
    uint8_t read8(uint32_t p){return uint8_t(read32(p&~3u)>>(24u-8u*(p&3u)));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=0x80006000u,msr=0x8032u,ctr=17,xer=0x80000000u,srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("pending IRQ witness");}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned i=0;i<18;++i){
        Cpu c;ExternalReturnWitness first;PendingExternalReentry next;
        c.mmu.words={{H,0x60000000u},{R,0x4c000064u},{ExternalVector,0x60000000u}};
        const std::array<uint8_t,4> vector{0x60,0,0,0};
        for(unsigned k=0;k<32;++k)c.gpr[k]=k*17+3;
        need(first.capture(c,Other|Mask,Mask));c.pc=R;c.srr0=H;c.srr1=c.msr;c.msr=0x32u;c.inst_count+=100;
        if(i==1)c.gpr[0]^=1u;
        const bool pre=first.before_pending_rfi(c,R,0x4c000064u,i==2?Other:Other|Mask,i==3?Mask|Other:Mask);
        if(i>=1&&i<=3){need(!pre&&first.failure()==2);++refused;continue;}need(pre);
        c.pc=H;c.msr=c.srr1;
        if(i==4)++c.inst_count;
        if(i==5)c.gpr[31]^=1u;
        if(i==6)c.msr^=1u;
        const bool ret=first.pending_rfi_return(c,Other|Mask,Mask);
        if(i>=4&&i<=6){need(!ret&&first.failure()==3);++refused;continue;}need(ret);
        if(i==7)c.mmu.words[ExternalVector]^=1u;
        const bool entered=next.enter(c,Other|Mask,Mask,vector,i!=8,i!=9);
        if(i>=7&&i<=9){need(!entered&&next.failure()==1);++refused;continue;}need(entered);
        if(i==10)c.srr0^=4;
        if(i==11)++c.inst_count;
        if(i==12)c.gqr[1]^=1;
        const bool poll=next.outer_poll(c,Other|Mask,Mask,i!=13);
        if(i>=10&&i<=13){need(!poll&&next.failure()==2);++refused;continue;}need(poll);
        if(i!=14)++c.inst_count;
        if(i==15)c.srr1^=1;
        const bool entry=next.vector_entry(c,ExternalVector,i==16?Other:Other|Mask,Mask,true);
        if(i>=14&&i<=16){need(!entry&&next.failure()==3);++refused;continue;}need(entry&&next.stage()==3&&next.captured().stage()==1&&c.pc==ExternalVector);
        if(i==17){need(!next.vector_entry(c,ExternalVector,Other|Mask,Mask,true));++refused;continue;}++valid;
    }
    need(valid==1&&refused==17);
    std::cout<<"V932_PENDING_REENTRY synthetic=1 valid=1 refused=17 original_execution=0\n";
}
