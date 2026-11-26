#include "wii_stm_final_return.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t Base=0x80000000u,Root=Base+0x100u,Start=Root+0x20u,Caller=Base+0x200u,
    Sp=Base+0x800u,Obj=Base+0x400u,Nop=0x60000000u,Ret=0x4e800020u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t Mtlr=0x7c0803a6u;
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
    uint32_t pc=Start,lr=Start,ctr=1,xer=2,msr=0x8032,srr0=Root,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[13]=Obj;c.gpr[30]=0x1234;c.gpr[31]=0x4321;
    const auto incoming=c.gpr;const auto cr=StmFinalReturnWitness::abi_cr(c);
    c.gpr[1]-=32;c.gpr[30]=9;c.gpr[31]=10;
    c.mmu.write32(Sp-32,fault==2?Sp+4:Sp);
    c.mmu.write32(Sp+4,fault==3?Caller+4:Caller);
    c.mmu.write32(Sp-8,incoming[30]);c.mmu.write32(Sp-4,incoming[31]);
    c.mmu.write32(Caller,Nop);
    const std::array<StmFinalSlot,3> slots{{{4,32},{-8,30},{-4,31}}};
    const std::array<uint32_t,9> code{{ins(14,0,0,fault==6?0:1),ins(14,3,0,0),
        ins(36,0,13,fault==7?8:4),ins(32,0,1,36),ins(32,30,1,24),
        ins(32,31,1,28),Mtlr,ins(14,1,1,32),Ret}};
    std::array<IpcDispatchWord,9> words{};
    for(unsigned i=0;i<code.size();++i){words[i]={Root,Start+4*i,code[i]};c.mmu.write32(words[i].pc,code[i]);}
    StmFinalReturnWitness w({Root,Start,Caller,Nop,32,Start+8,Obj+4,0,{Obj,16},slots,words});
    bool ok=w.begin(c,incoming,cr,fault!=1);
    if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok&&w.poll(c,true));
    if(fault==16||fault==17){
        ++c.inst_count;ok=w.entry(c,fault==17?Start+4:Start,true);
        if(fault==17){assert(!ok);return;}assert(ok);++c.inst_count;
    }else c.inst_count+=fault==4?1u:2u;
    ok=w.before(c,Start,fault==5?Nop:code[0],true);
    if(fault==4||fault==5){assert(!ok);return;}assert(ok);c.gpr[0]=fault==6?0:1;
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,Start+4*i,code[i],true);};
    assert(step(1));c.gpr[3]=0;ok=step(2);
    if(fault==6||fault==7){assert(!ok);return;}assert(ok);
    c.mmu.write32(Obj+4,fault==8?0:1);
    if(fault==9)c.mmu.write32(Obj+8,1);
    ok=step(3);if(fault==8||fault==9){assert(!ok);return;}assert(ok);
    c.gpr[0]=Caller;
    assert(step(4));c.gpr[30]=fault==10?0:incoming[30];
    ok=step(5);if(fault==10){assert(!ok);return;}assert(ok);c.gpr[31]=incoming[31];
    assert(step(6));c.lr=fault==11?Start:Caller;
    ok=step(7);if(fault==11){assert(!ok);return;}assert(ok);c.gpr[1]=fault==12?Sp-4:Sp;
    if(fault==13)c.gpr[29]^=1;
    ok=step(8);if(fault==12||fault==13){assert(!ok);return;}assert(ok);
    c.pc=fault==14?Caller+4:Caller;
    ok=w.poll(c,fault!=15);
    if(fault==14||fault==15){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==9&&w.loads()==3&&w.stores()==1);
    if(fault==18){++c.inst_count;assert(!w.reached(c,true));}
}
int main(){for(unsigned f=0;f<=18;++f)trial(f);
    std::cout<<"STM_FINAL_RETURN_TEST cases=19 original_execution=0\n";}
