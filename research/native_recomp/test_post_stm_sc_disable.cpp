#include "wii_post_stm_sc_disable.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t Base=0x80000000u,Root=Base+0x100u,Caller=Base+0x200u,Nop=0x60000000u;
constexpr uint32_t x(unsigned rs,unsigned ra,unsigned rb,unsigned xo){return (31u<<26)|(rs<<21)|(ra<<16)|(rb<<11)|(xo<<1);}
constexpr uint32_t rot(unsigned rs,unsigned ra,unsigned sh,unsigned mb,unsigned me){return (21u<<26)|(rs<<21)|(ra<<16)|(sh<<11)|(mb<<6)|(me<<1);}
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=Base&&a-Base<ram.size()?ram.data()+a-Base:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Root,lr=Caller,ctr=1,xer=2,msr=0x8032,srr0=Root,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Base+0x800u;c.gpr[31]=5u;
    std::array<uint32_t,5> code{{x(3,0,0,83),rot(3,4,0,17,fault==7?14:15),x(4,0,0,146),rot(3,3,17,31,31),0x4e800020u}};
    if(fault==8)code[2]=x(3,0,0,146);
    if(fault==15)code[3]=0x90610000u;
    std::array<IpcDispatchWord,5> words{};
    for(unsigned i=0;i<code.size();++i){words[i]={Root,Root+4*i,code[i]};c.mmu.write32(words[i].pc,code[i]);}
    c.mmu.write32(Caller,Nop);
    PostStmScDisableWitness w({Root,Caller,Nop,words});
    if(fault==2)c.msr&=~0x8000u;
    bool ok=w.begin(c,fault!=1);if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    if(fault==3)++c.inst_count;
    ok=w.poll(c,true);if(fault==3){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==4?Root+4:Root,true);
    if(fault==4){assert(!ok);return;}assert(ok);
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,Root+4*i,fault==5&&i==0?Nop:code[i],true);};
    ok=step(0);if(fault==5){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==6?0:c.msr;
    ok=step(1);if(fault==6){assert(!ok);return;}assert(ok);
    c.gpr[4]=fault==7?0x30u:0x32u;
    ok=step(2);if(fault==7||fault==8){assert(!ok);return;}assert(ok);
    c.msr=fault==9?0x8032u:fault==10?0x30u:0x32u;
    if(fault==11)c.gqr[4]^=1;
    ok=step(3);if(fault==9||fault==10||fault==11||fault==15){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==12?0:1;
    ok=step(4);if(fault==12){assert(!ok);return;}assert(ok);
    c.pc=fault==13?Caller+4:Caller;
    ok=w.poll(c,fault!=14);if(fault==13||fault==14){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==5&&w.expected_msr()==0x32u);
    if(fault==16){++c.inst_count;assert(!w.reached(c,true));}
}
int main(){for(unsigned i=0;i<=16;++i)trial(i);std::cout<<"POST_STM_SC_DISABLE_TEST cases=17 original_execution=0\n";}
