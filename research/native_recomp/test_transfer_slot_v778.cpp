#include "wii_si_handler_return_v725.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,Start=H+4u,Nop=0x60000000u,Call=0x48000ffdu,Blr=0x4e800020u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return (a>=H&&a<H+16u)||(a>=R&&a<R+4u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=R,msr=0x32u,srr0=0x80006000u,srr1=0x8032u,ctr=5,xer=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("V778 transfer slot");}
int main(){
    unsigned ok=0,bad=0;
    for(unsigned t=0;t<10;++t){
        Cpu c;c.mmu.words={{H,Nop},{Start,Call},{H+8,Nop},{H+12,Blr},{R,Nop}};
        SiHandlerReturnWitness w({H,H+16,Start,R,Nop});need(w.capture(c));c.pc=c.lr=Start;c.inst_count+=50;
        need(w.start(c,Start,true)&&w.before_authenticated(c,Start,Call,true,t==3?3u:4u));
        const unsigned n=t==1?128u:t==2?256u:t==4?257u:t==5?1u:130u;
        c.inst_count+=n+1u;c.pc=c.lr=H+8;
        if(t==6)++c.inst_count;
        if(t==7)c.lr=Start;
        if(t==8)c.msr|=0x8000u;
        bool ret=t==9?w.helper_returned(c,H+8,n,true,4):w.transfer_returned(c,H+8,n,t!=0);
        if(t==1||t==2){need(ret&&w.completed_calls()==8u&&w.before(c,H+8,Nop,true));++ok;}
        else{need(!ret&&w.failure()==8);++bad;}
    }
    need(ok==2&&bad==8);
    std::cout<<"V778_TRANSFER_SLOT synthetic=1 valid=2 refused=8 original_execution=0\n";
}
