#include "wii_stm_outer_restore.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,C=B+0x200u,Sp=B+0x600u;
constexpr uint32_t N=0x60000000u,MF=0x7c0000a6u,MT=0x7c000124u,ST=0x90010000u;
struct Mem{std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|*get_ptr(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=C,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault){
    Cpu c;std::array<IpcDispatchWord,4> words{{{R,R,MF},{R,R+4,N},{R,R+8,MT},{R,R+12,N}}};
    if(fault==3)words[1].word=ST;
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(C,N);c.gpr[1]=Sp;c.gpr[3]=fault==2?0u:1u;
    StmOuterRestoreWitness w({R,C,N,R+8,R+12,N,words});
    bool ok=w.begin(c,fault!=1);
    if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,true);};
    assert(step(R,MF));c.gpr[0]=c.msr;
    ok=step(R+4,words[1].word);if(fault==3){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==4?0x8033u:0x8032u;
    ok=step(R+8,MT);if(fault==4){assert(!ok);return;}assert(ok);
    c.pc=fault==5?R+8:R+12;c.msr=fault==6?0x32u:0x8032u;
    if(fault==7)c.gpr[4]=1;
    if(fault==8)++c.inst_count;
    if(fault==9)c.ctr=1;
    ok=w.poll(c,fault!=10,fault!=11);
    if(fault>=5&&fault<=11){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true,true)&&w.visits()==3u);
    if(fault==12){c.msr&=~0x8000u;assert(!w.reached(c,true,true));}
}
int main(){for(unsigned f=0;f<=12;++f)trial(f);std::cout<<"STM_OUTER_RESTORE_TEST cases=13 original_execution=0\n";}
