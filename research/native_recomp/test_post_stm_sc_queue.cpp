#include "wii_post_stm_sc_queue.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,S=R+20u,Q=B+0x200u,A=B+0x500u,Sp=B+0x900u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
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
    Cpu c;c.gpr[1]=Sp;
    const unsigned hi=fault==16?31u:3u;
    const std::array<IpcDispatchWord,7> words{{{R,S,ins(15,hi,0,0x8000)},
        {R,S+4,ins(14,3,hi,0x500)},{R,S+8,bl(S+8,Q)},
        {Q,Q,ins(14,0,0,0)},{Q,Q+4,ins(36,0,3,0)},
        {Q,Q+8,ins(36,0,3,fault==10?0:4)},{Q,Q+12,0x4e800020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(S+12,Nop);c.mmu.write32(A,0xdeadbeefu);c.mmu.write32(A+4,0x12345678u);
    c.mmu.write32(A+8,0xabcdef01u);
    ScQueueWitness w({R,S,Q,S+12,Nop,A,{A,fault==2?4u:12u},words});
    bool ok=w.begin(c,fault!=1);if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,S,true));
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,fault==3&&i==0?Nop:words[i].word,true);};
    ok=step(0);if(fault==3){assert(!ok);return;}assert(ok);
    c.gpr[hi]=0x80000000u;assert(step(1));c.gpr[3]=fault==4?A+4:A;
    ok=step(2);if(fault==4){assert(!ok);return;}assert(ok);
    c.pc=Q;c.lr=fault==5?S:S+12;
    ok=w.entry(c,Q,fault!=6);if(fault==5||fault==6){assert(!ok);return;}assert(ok);
    assert(step(3));c.gpr[0]=fault==7?1u:0u;
    ok=step(4);if(fault==7){assert(!ok);return;}assert(ok);
    c.mmu.write32(A,fault==8?1u:0u);if(fault==9)c.mmu.write32(A+8,0);
    ok=step(5);if(fault>=8&&fault<=10){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+4,fault==11?1u:0u);if(fault==12)c.gqr[4]^=1;
    ok=step(6);if(fault==11||fault==12){assert(!ok);return;}assert(ok);
    c.pc=fault==13?S+16:S+12;
    ok=w.poll(c,fault!=14);if(fault==13||fault==14){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==7&&w.stores()==2);
    assert(w.object_held(c,true));if(fault==15){c.mmu.write32(A+8,0);assert(!w.object_held(c,true));}
}
int main(){for(unsigned i=0;i<=16;++i)trial(i);std::cout<<"POST_STM_SC_QUEUE_TEST cases=17 original_execution=0\n";}
