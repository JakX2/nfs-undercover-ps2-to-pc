#include "wii_callback_frontier_v829.h"
#include <iostream>
#include <map>
#include <stdexcept>
using namespace undercover::wii;
constexpr uint32_t C=0x80006000u,A=0x80008000u,B=0x80009000u,Stack=0x80020000u;
constexpr uint32_t Stw=0x90810008u,Cond=0x41820008u;
constexpr auto bl=[](uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);};
constexpr std::array<CallbackFrontierWord,4> words{{{C,Stw},{C+4u,Cond},{C+8u,bl(C+8u,A)},{C+12u,bl(C+12u,B)}}};
constexpr CallbackFrontierExpectation expected{C,C+16u,C,words,{{{C+8u,A,3},{C+12u,B,5}}}};
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
    uint32_t pc=C,lr=C,msr=0x32u,srr0=0x80007000u,srr1=0x8032u,ctr=7,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
void need(bool b){if(!b)throw std::runtime_error("V829 witness");}
int main(){
    unsigned valid=0,refused=0;
    for(unsigned t=0;t<20;++t){
        Cpu c;for(auto x:words)c.mmu.put(x.pc,x.word);
        c.gpr[1]=Stack;c.gpr[2]=0x80021000u;c.gpr[13]=0x8070e8e0u;c.gpr[3]=2;c.gpr[4]=t==1?0x1234u:0u;
        c.cr[0].eq=t==2; c.mmu.put(Stack+8u,0xdeadbeefu);
        auto e=expected;
        if(t==3)c.mmu.put(C+12u,0);
        if(t==4)e.edges[1].ordinal=3;
        if(t==5)c.lr+=4;
        if(t==6)c.msr|=0x8000;
        CallbackFrontierWitness w(e);
        const auto started=w.start(c,C,Stw,t==7?4:2,t!=8,t!=9);
        if(t>=3&&t<=9){need(!started&&w.failure()==1);++refused;continue;}
        need(started);
        if(t==10)c.mmu.bytes.erase(Stack+8u);
        if(t==11)c.gpr[1]+=4;
        if(t==12)++c.inst_count;
        bool ok=w.before(c,C,Stw,true);
        if(t>=10&&t<=12){need(!ok&&w.failure()==(t==10?7u:2u));++refused;continue;}
        need(ok);c.mmu.put(Stack+8u,c.gpr[4]);++c.inst_count;
        if(t==13)c.mmu.put(Stack+8u,c.gpr[4]^1u);
        if(t==14)c.mmu.put(C+4u,Cond^1u);
        if(t==15)c.srr1^=4u;
        ok=w.before(c,C+4u,Cond,t!=16);
        if(t>=13&&t<=16){need(!ok&&w.failure()==(t==13?4u:t==14?3u:2u));++refused;continue;}
        need(ok);++c.inst_count;
        if(t==17)c.gpr[3]=3;
        if(t==18)c.gpr[4]=0x10000u;
        const auto pc=t==2||t==19?C+12u:C+8u;
        ok=w.before(c,pc,t==2||t==19?words[3].word:words[2].word,true);
        if(t>=17){need(!ok&&w.failure()==(t==19?2u:5u));++refused;continue;}
        need(ok&&w.stage()==2&&w.visits()==3&&w.writes()==1&&w.ordinal()==(t==2?5u:3u)&&w.zero_id()==unsigned(t==0));++valid;
    }
    need(valid==3&&refused==17);
    std::cout<<"V829_CALLBACK_FRONTIER synthetic=1 valid=3 refused=17 original_execution=0\n";
}
