#include "wii_ioctl_flush_tail_v1401.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
using R=OpenScRoute;
constexpr uint32_t A=R::EventInputCaller,B=R::EventOutputCaller,F=0x805222c0u,S=0x805195ecu,Q=0x90000100u,O=0x80010000u,N=0x60000000u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{std::map<uint32_t,uint32_t> words;uint32_t read32(uint32_t a){return words[a];}};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=A,lr=A,msr=0x32,ctr=0,dispatch_saved_ctx=0;
 uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=0x80020000u;
    const uint32_t w=fault==5?0x90610004u:N;
    std::array<ReplyNativeWord,7> words{{{A,A,w},{A,A+4,N},{A,B-4,bl(B-4,F)},
        {A,B,N},{A,B+4,N},{A,B+8,N},{A,B+12,bl(B+12,S)}}};
    for(auto x:words)c.mmu.words[x.pc]=x.word;
    c.mmu.words[F]=N;c.mmu.words[S]=N;
    IoctlFlushTailWitness t({{F,B,bl(B-4,F),N},{S,B+16,bl(B+12,S),N},words});
    if(fault==1)c.msr|=0x8000u;
    bool ok=t.begin(c,true,Q,O,32);
    if(fault==1){assert(!ok);return;}assert(ok);
    ++c.inst_count;if(fault==2)++c.inst_count;
    ok=t.before(c,A,w,fault!=3);
    if(fault==2||fault==3||fault==5){assert(!ok);return;}assert(ok);
    ++c.inst_count;assert(t.before(c,A+4,N,true));
    c.gpr[3]=fault==4?O+32:O;c.gpr[4]=32;
    ++c.inst_count;ok=t.before(c,B-4,bl(B-4,F),true);
    if(fault==4){assert(!ok);return;}assert(ok);
    c.pc=F;c.lr=fault==6?B+4:B;
    ok=t.entry(c,F,true);if(fault==6){assert(!ok);return;}assert(ok);
    c.pc=c.lr=B;c.inst_count+=20;if(fault==7)c.msr|=0x8000u;
    ok=t.output_return(c,true);if(fault==7){assert(!ok);return;}assert(ok);
    for(unsigned i=0;i<3;++i){++c.inst_count;assert(t.before(c,B+4*i,N,true));}
    c.gpr[3]=fault==8?Q+32:Q;++c.inst_count;
    ok=t.before(c,B+12,bl(B+12,S),true);if(fault==8){assert(!ok);return;}assert(ok);
    c.pc=S;c.lr=B+16;ok=t.entry(c,S,true);assert(ok&&t.reached(c,true)&&t.visits()==7);
    if(fault==9){c.gpr[3]+=32;assert(!t.reached(c,true));}
}
int main(){for(unsigned i=0;i<=9;++i)trial(i);std::cout<<"V1401_OUTPUT_TEST cases=10 original_execution=0\n";}
