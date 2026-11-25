#include "wii_callback_prefix_v800.h"
#include <array>
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t H=0x80004000u,C=0x80006000u,S=0x80008000u,Stack=0x80020000u;
constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,Bctrl=0x4e800421u;
constexpr uint32_t SaveCall=C+16u,Resume=C+20u,Branch=0x48000001u|((S-SaveCall)&0x03fffffcu);
constexpr std::array<uint32_t,6> prefix{0x9421ffc0u,0x7c0802a6u,0x90010044u,0x39610040u,Branch,Nop};
constexpr std::array<uint32_t,3> leaf{0x93cbfff8u,0x93ebfffcu,Blr};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;
    uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return words.contains(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=0x80009000u,msr=0x32u,srr0=0x80007000u,srr1=0x8032u,
             ctr=C,xer=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
void need(bool v){if(!v)throw std::runtime_error("V800 synthetic invariant");}
int main(){
    unsigned pass=0,refused=0;
    for(unsigned t=0;t<24;++t){
        Cpu c;
        for(unsigned i=0;i<32;++i)c.gpr[i]=0x1234567u*(i+1u);
        c.gpr[1]=Stack;c.mmu.words[H]=Bctrl;
        for(unsigned i=0;i<prefix.size();++i)c.mmu.words[C+4*i]=prefix[i];
        for(unsigned i=0;i<leaf.size();++i)c.mmu.words[S+4*i]=leaf[i];
        for(uint32_t a=Stack-0x400u;a<Stack+0x100u;a+=4u)c.mmu.words[a]=a^0xdeadbeefu;
        CallbackPrefixWitness<6,3> w(C,S,prefix,leaf);
        if(t==1){c.ctr|=3u;c.pc=H-4u;}
        if(t==2)c.ctr=S;
        if(t==3)c.mmu.words[C+4]^=1u;
        if(t==4)c.mmu.words.erase(Stack-4u);
        if(t==5)c.gpr[1]|=1u;
        const bool dispatcher=t>=16;
        if(t==17)c.ctr|=3u;
        const bool start=dispatcher?w.start_dispatch(c,H,Bctrl,true,true):w.start(c,H,Bctrl,t!=6,t!=7);
        if((t>=2&&t<=7)||t==17){need(!start&&w.failure()==1);++refused;continue;}
        need(start);
        c.pc=C;c.lr=H+4u;
        if(dispatcher){
            if(t==18)c.lr^=4u;
            if(t==19)++c.inst_count;
            if(t!=20){
                const bool polled=w.dispatch_poll(c,t!=21);
                if(t==18||t==19||t==21){need(!polled&&w.failure()==2);++refused;continue;}
                need(polled);
                if(t==22){need(!w.dispatch_poll(c,true)&&w.failure()==2);++refused;continue;}
            }
            if(t!=23)++c.inst_count;
            if(t==20||t==23){need(!w.entry(c,C,true)&&w.failure()==2);++refused;continue;}
        }
        if(t==8)++c.inst_count;
        if(t==9)c.gpr[3]^=1u;
        if(t==8||t==9){need(!w.entry(c,C,true)&&w.failure()==2);++refused;continue;}
        need(w.entry(c,C,true));
        auto step=[&](uint32_t pc,uint32_t word){
            if(t!=1||pc==Resume)c.pc=pc; // pinned linear code may retain entry PC
            ++c.inst_count;return w.before(c,pc,word,true);
        };
        need(step(C,prefix[0]));
        c.mmu.words[Stack-64u]=Stack;c.gpr[1]=Stack-64u;
        if(t==10)c.mmu.words[Stack-64u]^=1u;
        if(t==11)c.gpr[1]^=4u;
        if(t==10||t==11){need(!step(C+4,prefix[1])&&w.failure()==3);++refused;continue;}
        need(step(C+4,prefix[1]));c.gpr[0]=c.lr;
        need(step(C+8,prefix[2]));c.mmu.words[Stack+4u]=c.gpr[0];
        need(step(C+12,prefix[3]));c.gpr[11]=Stack;
        need(step(SaveCall,Branch));c.lr=Resume;c.pc=S;
        if(t==12)c.lr^=4u;
        if(t==12){need(!w.entry(c,S,true)&&w.failure()==2);++refused;continue;}
        need(w.entry(c,S,true));
        need(step(S,leaf[0]));c.mmu.words[Stack-8u]=c.gpr[30];
        need(step(S+4,leaf[1]));c.mmu.words[Stack-4u]=c.gpr[31];
        need(step(S+8,Blr));
        if(t==13)c.mmu.words[Stack-8u]^=1u;
        if(t==14)c.srr0^=4u;
        if(t==15){c.pc=Resume;++c.inst_count;need(!w.before(c,Resume,Nop,false)&&w.failure()==3);++refused;continue;}
        if(t==13||t==14){need(!step(Resume,Nop)&&w.failure()==3);++refused;continue;}
        need(step(Resume,Nop)&&w.stage()==6&&w.visits()==9&&w.writes()==4);
        ++pass;
    }
    need(pass==3&&refused==21);
    std::cout<<"V804_CALLBACK_PREFIX synthetic=1 valid=3 refused=21 dispatcher=1 original_execution=0\n";
}
