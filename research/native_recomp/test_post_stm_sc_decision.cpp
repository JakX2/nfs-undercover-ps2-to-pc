#include "wii_post_stm_sc_decision.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t Base=0x80000000u,Root=Base+0x100u,Start=Root+20u,Restore=Base+0x200u,
    Flag=Base+0x500u,State=Base+0x600u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t bl(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
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
    uint32_t pc=Start,lr=Start,ctr=1,xer=0,msr=0x32,srr0=Root,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Base+0x900u;c.gpr[3]=1u;c.gpr[13]=Base;
    const std::array<IpcDispatchWord,8> code{{
      {Root,Start,ins(32,0,13,0x500)},{Root,Start+4,ins(11,0,0,0)},
      {Root,Start+8,0x4182000cu},{Root,Start+12,bl(Start+12,Restore)},
      {Root,Start+20,ins(14,0,0,1)},{Root,Start+24,ins(36,0,13,0x500)},
      {Root,Start+28,ins(36,3,13,0x600)},{Root,Start+32,bl(Start+32,Restore)}}};
    std::array<ScDecisionCell,2> stores{{{Start+24,Flag,4,{Flag,8}},{Start+28,State,4,{State,8}}}};
    if(fault==3)stores[1].object={Flag,8};
    for(auto x:code)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Restore,Nop);if(fault==2)c.mmu.write32(Flag,1u);
    ScDecisionWitness w({Root,Start,Restore,Nop,Start+32,{Start,Flag,4,{Flag,8}},stores,code});
    bool ok=w.begin(c,fault!=1);if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok);
    if(fault==4)++c.inst_count;
    ok=w.poll(c,true);if(fault==4){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==5?Start+4:Start,true);
    if(fault==5){assert(!ok);return;}assert(ok);
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,code[i].pc,fault==6&&i==0?Nop:code[i].word,true);};
    ok=step(0);if(fault==6){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==7?1u:0u;
    ok=step(1);if(fault==7){assert(!ok);return;}assert(ok);
    c.cr[0].eq=fault!=8;c.cr[0].gt=fault==8;
    ok=step(2);if(fault==8){assert(!ok);return;}assert(ok);
    ok=step(fault==9?3:4);if(fault==9){assert(!ok);return;}assert(ok);
    c.gpr[0]=1u;assert(step(5));c.mmu.write32(Flag,fault==10?0:1);
    if(fault==11)c.mmu.write32(Flag+4,1);
    ok=step(6);if(fault==10||fault==11){assert(!ok);return;}assert(ok);
    c.mmu.write32(State,fault==12?0:1);if(fault==13)c.gqr[4]^=1;
    ok=step(7);if(fault==12||fault==13){assert(!ok);return;}assert(ok);
    c.pc=fault==14?Restore+4:Restore;c.lr=fault==15?Start:Start+36;
    ok=w.entry(c,c.pc,fault!=16);if(fault>=14&&fault<=16){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==7&&w.stores()==2);
    assert(w.objects_held(c,true));if(fault==17){c.mmu.write32(State+4,1);assert(!w.objects_held(c,true));}
}
int main(){for(unsigned i=0;i<=17;++i)trial(i);std::cout<<"POST_STM_SC_DECISION_TEST cases=18 original_execution=0\n";}
