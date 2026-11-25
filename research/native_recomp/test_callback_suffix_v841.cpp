#include "wii_callback_suffix_v841.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t C=0x80006000u,A=0x80008000u,Stack=0x80020000u;
constexpr uint32_t Stw=0x90810008u,Cond=0x41820008u,Bctrl=0x4e800421u;
constexpr auto bl=[](uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);};
constexpr std::array<CallbackSuffixWord,4> words{{{C,Stw},{C+4u,Cond},{C+8u,Bctrl},{C+12u,bl(C+12u,A)}}};
constexpr CallbackSuffixExpectation expected{C,C+16u,C,words,{{{C+8u,0,4},{C+12u,A,13}}}};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint8_t> bytes;
    uint8_t* get_ptr(uint32_t a){auto i=bytes.find(a);return i==bytes.end()?nullptr:&i->second;}
    uint8_t read8(uint32_t a){return bytes.at(a);}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void put(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)bytes[a+i]=uint8_t(v>>(24u-8u*i));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=C,lr=C,msr=0x32u,srr0=0x80007000u,srr1=0x8032u,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
void need(bool b){if(!b)throw std::runtime_error("V841 witness");}
Cpu seed(){
    Cpu c;for(auto x:words)c.mmu.put(x.pc,x.word);
    c.gpr[1]=Stack;c.gpr[2]=0x80021000u;c.gpr[13]=0x8070e8e0u;c.gpr[4]=0x12345678u;
    c.mmu.put(Stack+8u,0xdeadbeefu);c.mmu.put(A,0x60000000u);return c;
}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned t=0;t<18;++t){
        Cpu c=seed();auto e=expected;
        c.ctr=t==1?A+1u:t==2?A:t==3?0x90000000u:0u;
        c.cr[0].eq=t==4;
        if(t==5)c.mmu.put(C+12u,0);
        if(t==6)e.edges[1].ordinal=4;
        if(t==7)c.lr+=4;
        if(t==8)c.msr|=0x8000;
        CallbackSuffixWitness w(e);
        const auto started=w.start(c,C,Stw,t!=9,t!=10);
        if(t>=5&&t<=10){need(!started&&w.failure()==1);++refused;continue;}
        need(started);
        if(t==11)c.mmu.bytes.erase(Stack+8u);
        if(t==12)c.gpr[1]+=4;
        if(t==13)++c.inst_count;
        bool ok=w.before(c,C,Stw,true);
        if(t>=11&&t<=13){need(!ok&&w.failure()==(t==11?7u:2u));++refused;continue;}
        need(ok);c.mmu.put(Stack+8u,c.gpr[4]);++c.inst_count;
        if(t==14)c.mmu.put(Stack+8u,c.gpr[4]^1u);
        if(t==15)c.mmu.put(C+4u,Cond^1u);
        if(t==16)c.srr1^=4u;
        ok=w.before(c,C+4u,Cond,true);
        if(t>=14&&t<=16){need(!ok&&w.failure()==(t==14?4u:t==15?3u:2u));++refused;continue;}
        need(ok);++c.inst_count;
        const auto pc=t==4||t==17?C+12u:C+8u;
        ok=w.before(c,pc,t==4||t==17?words[3].word:words[2].word,true);
        if(t==17){need(!ok&&w.failure()==2u);++refused;continue;}
        need(ok&&w.stage()==2&&w.visits()==3&&w.writes()==1&&w.ordinal()==(t==4?13u:4u)&&w.target_class()==(t==4?0u:t+1u));++valid;
    }
    // Independent backward control path and same-tick dispatcher poll.
    constexpr uint32_t Bc=0x4182fffcu;
    const std::array<CallbackSuffixWord,4> loop{{{C,0x60000000u},{C+4u,Bc},{C+8u,Bctrl},{C+12u,bl(C+12u,A)}}};
    auto e=expected;e.words=loop;
    for(unsigned bad=0;bad<3;++bad){
        Cpu c=seed();for(auto row:loop)c.mmu.put(row.pc,row.word);c.cr[0].eq=true;
        CallbackSuffixWitness w(e);need(w.start(c,C,loop[0].word,true,true));
        need(w.before(c,C,loop[0].word,true));++c.inst_count;
        need(w.before(c,C+4u,Bc,true));
        if(bad==1)++c.inst_count;
        const bool ok=w.poll(c,true);
        if(bad==1){need(!ok&&w.failure()==2);++refused;continue;}
        need(ok);
        if(bad==2){need(!w.poll(c,true)&&w.failure()==2);++refused;continue;}
        ++c.inst_count;c.cr[0].eq=false;need(w.before(c,C,loop[0].word,true));++c.inst_count;
        need(w.before(c,C+4u,Bc,true));++c.inst_count;
        need(w.before(c,C+8u,Bctrl,true)&&w.stage()==2&&w.polls()==1&&w.visits()==5);++valid;
    }
    need(valid==6&&refused==15);
    std::cout<<"V841_CALLBACK_SUFFIX synthetic=1 valid=6 refused=15 original_execution=0\n";
}
