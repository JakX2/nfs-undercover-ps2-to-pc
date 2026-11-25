#include "wii_si_handler_return_v725.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,Nop=0x60000000u,Blr=0x4e800020u,Call=0x48001001u;
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=R,msr=0x32u,srr0=0x80006000u,srr1=0x8032u,ctr=5,xer=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void need(bool b){if(!b)throw std::runtime_error("V755 witness assertion");}
int main(){
    unsigned valid=0,rejected=0;
    for(unsigned trial=0;trial<16;++trial){
        Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*13u+9u;
        c.mmu.words={{H,Nop},{H+4,Call},{H+8,Call},{H+12,Blr},{R,Nop}};
        SiHandlerReturnWitness w({H,H+16,H+4,R,Nop});
        need(w.capture(c));c.pc=c.lr=H+4;c.inst_count+=50;need(w.start(c,c.pc,true));
        if(trial==2){need(!w.before_authenticated(c,c.pc,Call,true,0)&&w.failure()==8);++rejected;continue;}
        if(trial==3){need(!w.before_authenticated(c,c.pc,Call,true,13)&&w.failure()==8);++rejected;continue;}
        if(trial==4){need(!w.before(c,c.pc,Call,true)&&w.failure()==4);++rejected;continue;}
        if(trial==5){c.mmu.words[c.pc]=Nop;need(!w.before_authenticated(c,c.pc,Nop,true,3)&&w.failure()==8);++rejected;continue;}
        need(w.before_authenticated(c,c.pc,Call,true,3));
        c.pc=c.lr=H+8;c.inst_count+=46;
        if(trial==6){need(!w.helper_returned(c,c.pc,45,true,12)&&w.failure()==8);++rejected;continue;}
        if(trial==7){need(!w.helper_returned(c,c.pc,44,true,3)&&w.failure()==8);++rejected;continue;}
        if(trial==8){need(!w.before_authenticated(c,c.pc,Call,true,12)&&w.failure()==3);++rejected;continue;}
        if(trial==9){need(!w.helper_returned(c,c.pc,45,false,3)&&w.failure()==8);++rejected;continue;}
        need(w.helper_returned(c,c.pc,45,true,3)&&w.completed_calls()==4);
        if(trial==10){need(!w.before_authenticated(c,c.pc,Call,true,3)&&w.failure()==8);++rejected;continue;}
        if(trial==11){need(!w.helper_returned(c,c.pc,45,true,3)&&w.failure()==8);++rejected;continue;}
        const unsigned slot=trial==1?4u:12u;
        need(w.before_authenticated(c,c.pc,Call,true,slot));
        c.pc=c.lr=H+12;c.inst_count+=17;
        if(trial==12){need(!w.restore_returned(c,c.pc,20,true,slot)&&w.failure()==8);++rejected;continue;}
        if(trial==13){c.msr|=0x8000u;need(!w.restore_returned(c,c.pc,16,true,slot)&&w.failure()==8);++rejected;continue;}
        if(trial==14){c.pc+=4;need(!w.restore_returned(c,c.pc,16,true,slot)&&w.failure()==8);++rejected;continue;}
        need(w.restore_returned(c,c.pc,16,true,slot)&&w.completed_calls()==(4u|(1u<<(slot-1u))));
        c.lr=R;
        if(trial==15)c.gpr[17]^=1u;
        const bool ret=w.before(c,c.pc,Blr,true);
        if(trial==15){need(!ret&&w.failure()==5);++rejected;continue;}
        need(ret);c.pc=R;need(w.poll(c,true));c.inst_count+=2;
        need(w.resumed(c,R,Nop,true)&&w.stage()==5&&w.visits()==3);++valid;
    }
    need(valid==2&&rejected==14);
    std::cout<<"V755_HANDLER_CALL_SLOTS synthetic=1 valid=2 refused=14 distinct_calls=2 original_execution=0\n";
}
