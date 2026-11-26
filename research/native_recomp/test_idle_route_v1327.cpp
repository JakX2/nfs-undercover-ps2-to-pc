#include "wii_idle_route_v1327.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t E=0x80010000u,S=E+0x100,D=E+0x200,C=E+0x300,B=E+0x400,T=E+0x500,L=E+0x600;
constexpr uint32_t Nop=0x60000000u,Blr=0x4e800020u,Bctrl=0x4e800421u,Mtmsr=0x7c600124u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu{std::map<uint32_t,uint32_t> m;uint8_t byte=0;uint8_t* get_ptr(uint32_t a){return m.count(a&~3u)?&byte:nullptr;}uint32_t read32(uint32_t a){return m.at(a);}};
struct Flag{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Flag,8> cr{};uint32_t pc=E+4,lr=S,ctr=B,msr=0x8032,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned f){
    Cpu c;const std::array<ReplyNativeWord,13> words{{
        {E,E+4,Blr},{S,S,bl(S,D)},{D,D,Mtmsr},{D,D+4,Blr},
        {S,S+4,bl(S+4,C)},{C,C,Blr},{S,S+8,Bctrl},{B,B,Blr},
        {S,S+12,bl(S+12,T)},{T,T,Blr},{S,S+16,bl(S+16,L)},{L,L,Nop},{S,S+20,Nop}}};
    const std::array<VectorEdge,4> direct{{{D,S+4,bl(S,D),Mtmsr},{C,S+8,bl(S+4,C),Blr},{T,S+16,bl(S+12,T),Blr},{L,S+20,bl(S+16,L),Nop}}};
    const std::array<VectorEdge,1> indirect{{{B,S+12,Bctrl,Blr}}};
    for(auto w:words)c.mmu.m[w.pc]=w.word;
    IdleRouteWitness route({E,E+4,S,S,L,words,direct,indirect});
    assert(route.begin(c,true));
    if(f==1){++c.inst_count;assert(!route.poll(c,true)&&route.failure()==5);return;}
    assert(route.poll(c,true));
    auto step=[&](uint32_t pc,uint32_t w,unsigned ticks=1){c.inst_count+=ticks;return route.before(c,pc,w,true);};
    if(f==2){assert(!step(E+4,Blr)&&route.failure()==3);return;}
    assert(step(E+4,Blr,2));c.pc=S;assert(route.poll(c,true));
    assert(step(S,bl(S,D),2));c.pc=D;c.lr=S+4;
    if(f==3){++c.inst_count;assert(!route.entry(c,D,true));return;}
    assert(route.entry(c,D,true));c.gpr[3]=f==4?0x8032u:0x32u;
    bool ok=step(D,Mtmsr);if(f==4){assert(!ok&&route.failure()==4);return;}assert(ok);c.msr=0x32;
    assert(step(D+4,Blr));assert(step(S+4,bl(S+4,C)));c.pc=C;c.lr=S+8;
    assert(route.entry(c,C,true));assert(step(C,Blr));
    if(f==5)c.ctr=B+4;
    ok=step(S+8,Bctrl);if(f==5){assert(!ok&&route.failure()==4);return;}assert(ok);
    c.pc=B;c.lr=S+12;assert(route.poll(c,true));++c.inst_count;assert(route.entry(c,B,true));
    if(f==6){assert(!step(B,Blr,2));return;}
    assert(step(B,Blr));c.pc=S+12;assert(route.poll(c,true));
    if(f==7)c.mmu.m[S+12]=Nop;
    ok=step(S+12,bl(S+12,T),2);if(f==7){assert(!ok&&route.failure()==3);return;}assert(ok);
    c.pc=T;c.lr=S+16;assert(route.entry(c,T,true));assert(step(T,Blr));assert(step(S+16,bl(S+16,L)));
    c.pc=L;c.lr=S+20;assert(route.entry(c,L,true)&&route.loader_at(c,true));
    if(f==8){++c.inst_count;assert(!route.loader_at(c,true));}
    else assert(f==0&&route.visits()==11u);
}
int main(){for(unsigned f=0;f<=8;++f)trial(f);std::cout<<"V1327_IDLE_ROUTE synthetic=1 valid=1 refused=8 direct=4 indirect=1 original_execution=0\n";}
