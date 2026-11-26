#include "wii_post_stm_sc_leaf_shadow.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,L=B+0x200u,A=B+0x500u,Sp=B+0x900u,Nop=0x60000000u;
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
    uint32_t pc=R,lr=L,ctr=1,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
// Synthetic independent native-state driver; no owner code.
static void conditional(unsigned fault,bool early){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=A;c.gpr[4]=early?0u:1u;
    c.mmu.write32(A,0x00800000u);c.mmu.write32(L,Nop);
    const std::array<IpcDispatchWord,6> words{{{R,R,ins(11,0,4,0)},
        {R,R+4,fault==7?0x4c820020u:0x4d820020u},
        {R,R+8,ins(35,5,3,1)},{R,R+12,0x7ca30774u},
        {R,R+16,ins(11,0,3,-128)},{R,R+20,0x4d820020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    const std::array<uint32_t,6> path{{R,R+4,R+8,R+12,R+16,R+20}};
    const std::array<uint32_t,6> badpath{{R,R+4,R+12,R+8,R+16,R+20}};
    const std::array<ScLeafAccess,1> reads{{{R+8,1,1,fault==6}}};
    const auto p=std::span<const uint32_t>(fault==5?badpath:path).first(early?2u:6u);
    const auto a=std::span<const ScLeafAccess>(reads).first(early?0u:1u);
    const uint32_t expected=early?A:fault==4?0u:0xffffff80u;
    ScLeafShadow w({R,L,Nop,words,a,0,0,0,p,true,expected});
    bool ok=w.begin(c,{A,4},true);if(fault==6){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,words[i].word,true);};
    assert(step(0));c.cr[0].eq=early;c.cr[0].gt=!early;
    ok=step(1);if(fault==5||fault==7){assert(!ok);return;}assert(ok);
    if(early){c.pc=L;assert(w.poll(c,true)&&w.reached(c,true)&&w.visits()==2);return;}
    assert(step(2));c.gpr[3]+=1;c.gpr[5]=fault==1?0u:0x80u;
    ok=step(3);if(fault==1){assert(!ok);return;}assert(ok);
    c.gpr[3]=0xffffff80u;if(fault==2)c.mmu.write32(A,0);
    ok=step(4);if(fault==2){assert(!ok);return;}assert(ok);
    c.cr[0].eq=true;c.cr[0].gt=false;assert(step(5));c.pc=fault==3?L+4:L;
    ok=w.poll(c,true);if(fault==3||fault==4){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.visits()==6&&w.loads()==1&&w.stores()==0);
}
int main(){conditional(0,true);for(unsigned i=0;i<=7;++i)conditional(i,false);
    std::cout<<"POST_STM_SC_FORMATTER_LEAF_SHADOW_TEST cases=9 original_execution=0\n";}
