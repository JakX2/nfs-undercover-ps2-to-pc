#include "wii_ioctl_submit_prefix_v1403.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t W=0x80000100u,S=0x80001000u,C=0x80002000u,F=0x80003000u,SP=0x80008000u,Q=0x90000100u;
constexpr uint32_t N=0x60000000u,Push=0x9421ffe0u,Zero=0x38000000u,St0=0x90030000u,St4=0x90030004u,Blr=0x4e800020u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{
    std::vector<uint8_t> one=std::vector<uint8_t>(0x10000),two=std::vector<uint8_t>(0x1000);
    uint8_t* get_ptr(uint32_t a){if(a>=0x80000000u&&a-0x80000000u<one.size())return one.data()+a-0x80000000u;if(a>=0x90000000u&&a-0x90000000u<two.size())return two.data()+a-0x90000000u;return nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=W+4,msr=0x32,ctr=0,dispatch_saved_ctx=0;
 uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(bool heap,unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=Q;const uint32_t queue=heap?Q+48:SP-16;
    std::array<ReplyNativeWord,8> words{{{S,S,Push},{S,S+4,bl(S+4,C)},{S,S+8,N},{S,S+12,bl(S+12,F)},
        {C,C,Zero},{C,C+4,St0},{C,C+8,St4},{C,C+12,Blr}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(W,bl(W,S));c.mmu.write32(F,N);c.mmu.write32(queue,0xdead);c.mmu.write32(queue+4,0xbeef);
    IoctlSubmitPrefixWitness w({{S,W+4,bl(W,S),Push},{C,S+8,bl(S+4,C),Zero},{F,S+16,bl(S+12,F),N},words});
    if(fault==1)c.msr|=0x8000u;
    bool ok=w.begin(c,true,Q,64);if(fault==1){assert(!ok);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,S,Push,true));c.mmu.write32(SP-32,fault==2?0u:SP);c.gpr[1]=SP-32;
    c.gpr[3]=fault==3?0x80009000u:queue;++c.inst_count;
    ok=w.before(c,S+4,bl(S+4,C),true);if(fault==2||fault==3){assert(!ok);return;}assert(ok);
    c.pc=C;c.lr=fault==4?S+12:S+8;
    ok=w.entry(c,C,true);if(fault==4){assert(!ok);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,C,Zero,true));c.gpr[0]=fault==5?1u:0u;
    ++c.inst_count;ok=w.before(c,C+4,St0,true);if(fault==5){assert(!ok);return;}assert(ok);
    c.mmu.write32(queue,fault==6?1u:0u);
    ++c.inst_count;ok=w.before(c,C+8,St4,true);if(fault==6){assert(!ok);return;}assert(ok);
    c.mmu.write32(queue+4,0);++c.inst_count;assert(w.before(c,C+12,Blr,true));
    c.gpr[3]=Q;++c.inst_count;ok=w.before(c,S+8,N,fault!=7);if(fault==7){assert(!ok);return;}assert(ok);
    if(fault==9)c.mmu.write32(Q+8,1);
    c.gpr[4]=fault==8?16u:64u;++c.inst_count;
    ok=w.before(c,S+12,bl(S+12,F),true);if(fault==8||fault==9){assert(!ok);return;}assert(ok);
    c.pc=F;c.lr=S+16;assert(w.entry(c,F,true)&&w.reached(c,true)&&w.queue_stores()==2u&&w.stores()==3u);
    assert(w.request_stores()==(heap?2u:0u));
}
static void skip_trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=Q;
    constexpr uint32_t J=S+4,K=S+8,T=S+12,L=S+16;
    const uint32_t jump=0x41820000u|((T-J)&0xfffcu);
    const std::array<ReplyNativeWord,9> words{{{S,S,Push},{S,J,jump},{S,K,bl(K,C)},{S,T,N},{S,L,bl(L,F)},
        {C,C,Zero},{C,C+4,St0},{C,C+8,St4},{C,C+12,Blr}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(W,bl(W,S));c.mmu.write32(F,N);
    IoctlSubmitPrefixWitness w({{S,W+4,bl(W,S),Push},{C,K+4,bl(K,C),Zero},{F,L+4,bl(L,F),N},words});
    assert(w.begin(c,true,Q,64,fault==1?0u:fault==2?0x80009001u:0x80009000u));
    ++c.inst_count;assert(w.before(c,S,Push,true));c.mmu.write32(SP-32,SP);c.gpr[1]=SP-32;
    c.cr[0].eq=fault!=3;++c.inst_count;
    bool ok=w.before(c,J,jump,true);
    if(fault==1||fault==2){assert(!ok&&w.detail()==6);return;}assert(ok);
    ++c.inst_count;ok=w.before(c,T,N,true);
    if(fault==3){assert(!ok);return;}assert(ok&&w.queue_path()==2u);
    c.gpr[3]=Q;c.gpr[4]=64;
    if(fault==4)c.mmu.write32(Q+8,1);
    ++c.inst_count;ok=w.before(c,L,bl(L,F),true);
    if(fault==4){assert(!ok&&w.detail()==4);return;}assert(ok);
    c.pc=F;c.lr=L+4;assert(w.entry(c,F,true)&&w.reached(c,true)&&w.queue_stores()==0u&&w.queue_path()==2u);
}
int main(){for(bool heap:{false,true})for(unsigned f=0;f<=9;++f)trial(heap,f);
    for(unsigned f=0;f<=4;++f)skip_trial(f);
    std::cout<<"V1403_SUBMIT_PREFIX_TEST cases=25 original_execution=0\n";}
