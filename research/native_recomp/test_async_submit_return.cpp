#include "wii_async_submit_return.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,S=B+0x100u,R=B+0x200u,C=B+0x300u,Sp=B+0x600u;
constexpr uint32_t N=0x60000000u,Ret=0x4e800020u,MSR=0x7c000124u,MTLR=0x7c0803a6u,ST=0x90010000u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);v=(v<<8)|*p;}return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=S,lr=S,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault){
    Cpu c;
    std::array<IpcDispatchWord,8> words{{{S,S,N},{S,S+4,bl(S+4,R)},{S,S+8,MTLR},{S,S+12,N},{S,S+16,Ret},{R,R,MSR},{R,R+4,Ret},{C,C,N}}};
    if(fault==2)words[0].word=ST;
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.gpr[1]=Sp;
    AsyncSubmitReturnWitness w({S,S,C,N,{S+4,R,bl(S+4,R)},words});
    bool ok=w.begin(c,fault!=1,Sp+64);if(fault==1){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,true);};
    ok=step(S,words[0].word);if(fault==2){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==3?1u:0u;ok=step(S+4,bl(S+4,R));if(fault==3){assert(!ok);return;}assert(ok);
    c.pc=R;c.lr=fault==4?S:S+8;ok=w.entry(c,R,true);if(fault==4){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==5?0x8032u:c.msr;ok=step(R,MSR);if(fault==5){assert(!ok);return;}assert(ok);
    c.pc=R+4;assert(w.poll(c,true));if(fault==6){assert(!w.poll(c,true));return;}
    if(fault==7)c.gpr[31]=1;
    ok=step(R+4,Ret);if(fault==7){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==8?C+4:C;ok=step(S+8,MTLR);if(fault==8){assert(!ok);return;}assert(ok);
    c.lr=C;assert(step(S+12,N));c.gpr[1]=fault==9?Sp:Sp+64;
    ok=step(S+16,Ret);if(fault==9){assert(!ok);return;}assert(ok);
    c.pc=C;ok=w.returned(c,C,true,fault!=10);if(fault==10){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true,true)&&w.visits()==7&&w.polls()==1);
    if(fault==11){c.msr|=0x8000;assert(!w.reached(c,true,true));}
}
int main(){for(unsigned f=0;f<=11;++f)trial(f);std::cout<<"ASYNC_SUBMIT_RETURN_TEST cases=12 original_execution=0\n";}
