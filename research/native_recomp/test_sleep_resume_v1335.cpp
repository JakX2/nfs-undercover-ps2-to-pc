#include "wii_sleep_resume_v1335.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t S=0x80010000u,W=S+0x100u,R=S+0x200u,Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu{std::map<uint32_t,uint32_t> m;uint8_t byte=0;uint8_t* get_ptr(uint32_t a){return m.count(a&~3u)?&byte:nullptr;}uint32_t read32(uint32_t a){return m.at(a);}};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=W,ctr=0,msr=0x32,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
struct Load{bool ok=true;bool restored(Cpu&,bool held)const{return ok&&held;}};
static void trial(unsigned f){
    Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*17u;c.gpr[1]=0x80050000u;c.gpr[3]=0;
    auto original=c.gpr;
    const std::array<ReplyNativeWord,5> words{{{S,S+4,Nop},{S,S+8,Blr},{W,W,Nop},{W,W+4,bl(W+4,R)},{R,R,Nop}}};
    for(auto w:words)c.mmu.m[w.pc]=w.word;
    SleepResumeWitness w({S,W,S+4,W,{R,W+8,bl(W+4,R),Nop},words});
    if(f==1)c.lr+=4;
    bool ok=w.capture(c,true);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    c.pc=S+4;c.gpr[1]-=64;c.gpr[3]=1;c.inst_count+=100;
    if(f==2)c.gpr[1]=original[1];
    ok=w.begin(c,Load{f!=3},true);if(f==2||f==3){assert(!ok&&w.failure()==2);return;}assert(ok);
    assert(w.poll(c,true));c.inst_count+=f==4?1:2;
    ok=w.before(c,S+4,Nop,true);if(f==4){assert(!ok&&w.failure()==3);return;}assert(ok);
    c.gpr=original;c.gpr[3]=1;if(f==5)c.gpr[31]^=1;++c.inst_count;
    ok=w.before(c,S+8,Blr,true);if(f==5){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.pc=W;assert(w.poll(c,true));c.inst_count+=2;assert(w.before(c,W,Nop,true));
    c.gpr[3]=f==6?1:0;++c.inst_count;ok=w.before(c,W+4,bl(W+4,R),true);
    if(f==6){assert(!ok&&w.failure()==5);return;}assert(ok);
    c.pc=R;c.lr=W+8;if(f==7)c.lr+=4;
    ok=w.entry(c,R,true);if(f==7){assert(!ok&&w.failure()==7);return;}assert(ok);
    assert(w.restored_sleep_at(c,true)&&w.visits()==4);
    if(f==8){++c.inst_count;assert(!w.restored_sleep_at(c,true));}
}
int main(){for(unsigned f=0;f<=8;++f)trial(f);std::cout<<"V1335_SLEEP_RESUME synthetic=1 valid=1 refused=8 original_execution=0\n";}
