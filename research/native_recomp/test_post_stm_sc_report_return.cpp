#include "wii_post_stm_sc_report_return.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,S=R+100u,C=B+0x400u,Sp=B+0x900u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
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
    uint32_t pc=S,lr=S,ctr=1,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Sp-128;c.mmu.write32(Sp-128,fault==2?0:Sp);c.mmu.write32(Sp+4,fault==3?0:C);
    const std::array<IpcDispatchWord,4> words{{{R,S,ins(32,0,1,fault==7?128:132)},
        {R,S+4,0x7c0803a6u},{R,S+8,ins(14,1,1,fault==10?124:128)},{R,S+12,0x4e800020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(C,Nop);const std::array<StmFinalSlot,1> slots{{{4,32}}};
    ScReportReturnWitness w({R,S,C,Nop,128,words,slots});
    auto incoming=c.gpr;incoming[1]=Sp;
    bool ok=w.begin(c,incoming,fault!=1);if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok);
    if(fault==4)++c.inst_count;
    ok=w.poll(c,true);if(fault==4){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==5?S+4:S,true);
    if(fault==5){assert(!ok);return;}assert(ok);
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,fault==6&&i==0?Nop:words[i].word,true);};
    ok=step(0);if(fault==6||fault==7){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==8?0:C;ok=step(1);if(fault==8){assert(!ok);return;}assert(ok);
    c.lr=fault==9?S:C;ok=step(2);if(fault==9||fault==10){assert(!ok);return;}assert(ok);
    c.gpr[1]=fault==11?Sp-4:Sp;if(fault==12)c.mmu.write32(Sp-4,1);
    ok=step(3);if(fault==11||fault==12){assert(!ok);return;}assert(ok);
    c.pc=fault==13?C+4:C;if(fault==14)c.gqr[4]^=1;
    ok=w.poll(c,fault!=15);if(fault>=13&&fault<=15){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.visits()==4&&w.loads()==1&&w.expected_sp()==Sp);
}
static void nonvolatile(unsigned fault){
    Cpu c;c.gpr[1]=Sp-128;c.gpr[31]=0x1234;auto incoming=c.gpr;incoming[1]=Sp;incoming[31]=0x5678;
    c.mmu.write32(Sp-128,Sp);c.mmu.write32(Sp+4,C);c.mmu.write32(Sp-4,fault==1?0:incoming[31]);
    const std::array<IpcDispatchWord,5> words{{{R,S,ins(32,0,1,132)},
        {R,S+4,ins(32,fault==2?30:31,1,124)},{R,S+8,0x7c0803a6u},
        {R,S+12,ins(14,1,1,128)},{R,S+16,0x4e800020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(C,Nop);
    const std::array<StmFinalSlot,2> slots{{{4,32},{-4,31}}};
    ScReportReturnWitness w({R,S,C,Nop,128,words,slots});
    bool ok=w.begin(c,incoming,true);if(fault==1){assert(!ok);return;}assert(ok&&w.poll(c,true));
    ++c.inst_count;assert(w.entry(c,S,true));
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,words[i].word,true);};
    assert(step(0));c.gpr[0]=C;ok=step(1);if(fault==2){assert(!ok);return;}assert(ok);
    c.gpr[31]=fault==3?0:incoming[31];ok=step(2);if(fault==3){assert(!ok);return;}assert(ok);
    c.lr=C;assert(step(3));c.gpr[1]=Sp;assert(step(4));c.pc=C;
    assert(w.poll(c,true)&&w.reached(c,true)&&w.loads()==2);
}
int main(){for(unsigned i=0;i<=15;++i)trial(i);for(unsigned i=0;i<=3;++i)nonvolatile(i);
    std::cout<<"POST_STM_SC_REPORT_RETURN_TEST cases=20 original_execution=0\n";}
