#include "wii_post_stm_sc_version.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,Root=B+0x100u,Start=Root+20u,Version=B+0x200u,Report=B+0x300u,
    Cell=B+0x500u,Str=B+0x600u,Fmt=B+0x700u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t branch(uint32_t pc,uint32_t dst,bool link){return 0x48000000u|((dst-pc)&0x03fffffcu)|unsigned(link);}
constexpr uint32_t mr(unsigned ra,unsigned rs){return (31u<<26)|(rs<<21)|(ra<<16)|(rs<<11)|(444u<<1);}
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Start,lr=Start,ctr=1,xer=0,msr=0x8032,srr0=Root,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=B+0x900u;c.gpr[13]=B;
    std::array<IpcDispatchWord,5> words{{{Root,Start,ins(32,3,13,0x500)},
        {Root,Start+4,branch(Start+4,Version,true)},{Version,Version,mr(4,3)},
        {Version,Version+4,ins(14,3,13,0x700)},{Version,Version+8,branch(Version+8,Report,fault==12)}}};
    std::array<ScVersionByte,9> data{{{Cell,0x80},{Cell+1,0},{Cell+2,6},{Cell+3,0},{Str,'V'},{Str+1,0},{Fmt,'%'},{Fmt+1,'s'},{Fmt+2,0}}};
    for(auto x:data)*c.mmu.get_ptr(x.addr)=x.value;
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Report,Nop);if(fault==2)c.mmu.write32(Cell,0);
    if(fault==3)data[8]=data[7];
    ScVersionWitness w({Root,Start,Version,Report,Nop,Cell,Str,Fmt,words,data});
    bool ok=w.begin(c,fault!=1);if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok);
    if(fault==4)++c.inst_count;
    ok=w.poll(c,true);if(fault==4){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==5?Start+4:Start,true);
    if(fault==5){assert(!ok);return;}assert(ok);
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,fault==6&&i==0?Nop:words[i].word,true);};
    ok=step(0);if(fault==6){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==7?0:Str;
    ok=step(1);if(fault==7){assert(!ok);return;}assert(ok);
    c.pc=Version;c.lr=fault==8?Start:Start+8;
    ok=w.entry(c,Version,true);if(fault==8){assert(!ok);return;}assert(ok);
    assert(step(2));c.gpr[4]=fault==9?0:Str;if(fault==10)*c.mmu.get_ptr(Str)='X';
    ok=step(3);if(fault==9||fault==10){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==11?0:Fmt;
    ok=step(4);if(fault==11||fault==12){assert(!ok);return;}assert(ok);
    c.pc=fault==13?Report+4:Report;if(fault==14)c.lr=Version+12;if(fault==15)c.gqr[4]^=1;
    ok=w.poll(c,fault!=16);if(fault>=13&&fault<=16){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==5);
    assert(w.data_held(c,true));if(fault==17){*c.mmu.get_ptr(Fmt)='X';assert(!w.data_held(c,true));}
}
int main(){for(unsigned i=0;i<=17;++i)trial(i);std::cout<<"POST_STM_SC_VERSION_TEST cases=18 original_execution=0\n";}
