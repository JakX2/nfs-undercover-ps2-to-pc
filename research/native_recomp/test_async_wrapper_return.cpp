#include "wii_async_wrapper_return.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,S=B+0x100u,R=B+0x200u,C=B+0x300u,Sp=B+0x600u;
constexpr uint32_t N=0x60000000u,Ret=0x4e800020u,MTLR=0x7c0803a6u,ST=0x90010000u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
constexpr uint32_t lw(unsigned rs,unsigned ra,unsigned off){return (32u<<26)|(rs<<21)|(ra<<16)|off;}
struct Mem{std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=S,lr=S,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault){
    Cpu c;
    std::array<IpcDispatchWord,10> words{{{S,S,N},{S,S+4,bl(S+4,R)},{S,S+8,lw(0,1,68)},
        {S,S+12,MTLR},{S,S+16,N},{S,S+20,Ret},{R,R,lw(30,11,0)},{R,R+4,lw(31,11,4)},
        {R,R+8,Ret},{C,C,N}}};
    if(fault==2)words[0].word=ST;
    if(fault==3)words[6].word=lw(29,11,0);
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.gpr[1]=Sp;c.gpr[11]=Sp+16;c.mmu.write32(Sp+16,77);c.mmu.write32(Sp+20,88);c.mmu.write32(Sp+68,C);
    AsyncWrapperReturnWitness w({S,S,C,N,2,{S+4,R,bl(S+4,R)},words});
    bool ok=w.begin(c,fault!=1,Sp+64);if(fault==1){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,true);};
    ok=step(S,words[0].word);if(fault==2){assert(!ok);return;}assert(ok);
    assert(step(S+4,bl(S+4,R)));c.pc=R;c.lr=fault==4?S:S+8;
    ok=w.entry(c,R,true);if(fault==4){assert(!ok);return;}assert(ok);
    if(fault==5)c.gpr[11]=Sp+128;
    ok=step(R,words[6].word);if(fault==3||fault==5){assert(!ok);return;}assert(ok);
    c.gpr[30]=fault==6?0u:77u;
    ok=step(R+4,words[7].word);if(fault==6){assert(!ok);return;}assert(ok);
    c.gpr[31]=88;
    if(fault==7)c.mmu.write32(Sp+8,1);
    ok=step(R+8,Ret);if(fault==7){assert(!ok);return;}assert(ok);
    assert(step(S+8,words[2].word));c.gpr[0]=C;
    assert(step(S+12,MTLR));c.lr=C;assert(step(S+16,N));c.gpr[1]=fault==8?Sp:Sp+64;
    ok=step(S+20,Ret);if(fault==8){assert(!ok);return;}assert(ok);
    c.pc=C;ok=w.returned(c,C,true,fault!=9);if(fault==9){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true,true)&&w.visits()==9&&w.loads()==3&&w.restored()==2);
    if(fault==10){c.msr|=0x8000;assert(!w.reached(c,true,true));}
}
int main(){for(unsigned f=0;f<=10;++f)trial(f);std::cout<<"ASYNC_WRAPPER_RETURN_TEST cases=11 original_execution=0\n";}
