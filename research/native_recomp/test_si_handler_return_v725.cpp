#include "wii_si_handler_return_v725.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,R=0x80005000u,Start=H+4u,Nop=0x60000000u,Blr=0x4e800020u,
    Cond=0x4082fffcu,External=0x48000ff8u,Call=0x48000005u;
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
static void need(bool b){if(!b)throw std::runtime_error("V725 witness assertion");}
int main(){
    unsigned valid=0,rejected=0;
    for(unsigned trial=0;trial<20;++trial){
        Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*13u+9u;
        c.mmu.words={{H,Nop},{Start,Nop},{H+8,Cond},{H+12,Blr},{R,Nop}};
        if(trial==3)c.mmu.words[H+8]=Call;
        if(trial==4)c.mmu.words[H+8]=External;
        SiHandlerReturnWitness w({H,H+16,Start,R,Nop});
        need(w.capture(c));c.pc=c.lr=Start;c.inst_count+=50;
        if(trial==5){need(!w.start(c,Start,false));++rejected;continue;}
        need(w.start(c,Start,true)&&w.before(c,Start,Nop,true));
        ++c.inst_count;
        if(trial==6){need(!w.before(c,H+12,Blr,true));++rejected;continue;}
        if(trial==3||trial==4){
            need(!w.before(c,H+8,c.mmu.words[H+8],true)&&w.failure()==4);++rejected;continue;
        }
        c.cr[0].eq=trial!=1;
        need(w.before(c,H+8,Cond,true)&&w.pending());c.pc=H+8;
        if(trial==7)c.ctr^=1u;
        if(trial==8)c.gpr[3]^=1u;
        if(trial==9)c.srr1^=1u;
        if(trial==10)c.pc=H;
        if(trial==11)++c.inst_count;
        if(trial>=7&&trial<=11){need(!w.poll(c,true));++rejected;continue;}
        if(trial==12){need(!w.poll(c,false));++rejected;continue;}
        if(trial==13){++c.inst_count;need(!w.before(c,H+12,Blr,true));++rejected;continue;}
        need(w.poll(c,true));
        if(trial==14){need(!w.poll(c,true));++rejected;continue;}
        ++c.inst_count;
        if(trial==1){
            need(w.before(c,Start,Nop,true));++c.inst_count;c.cr[0].eq=true;
            need(w.before(c,H+8,Cond,true));c.pc=H+8;need(w.poll(c,true));++c.inst_count;
        }
        if(trial==15){need(!w.before(c,Start,Nop,true));++rejected;continue;}
        c.lr=R;
        if(trial==16)c.gpr[14]^=1u;
        if(trial==17)c.cr[2].eq=true;
        if(trial==16||trial==17){need(!w.before(c,H+12,Blr,true)&&w.failure()==5);++rejected;continue;}
        need(w.before(c,H+12,Blr,true));c.pc=R;
        if(trial==18){c.lr=H;need(!w.poll(c,true));++rejected;continue;}
        need(w.poll(c,true));
        c.inst_count+=2;
        if(trial==19){++c.inst_count;need(!w.resumed(c,R,Nop,true));++rejected;continue;}
        need(w.resumed(c,R,Nop,true)&&w.stage()==5&&w.visits()==(trial==1?5u:3u));
        ++valid;
    }
    need(valid==3&&rejected==17);
    std::cout<<"V725_HANDLER_RETURN synthetic=1 valid=3 refused=17 original_execution=0\n";
}
