#include "wii_sleep_exit_v1339.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t S=0x80010000u,R=S+0x100u,U=S+0x200u,Nop=0x60000000u,Blr=0x4e800020u,Mtmsr=0x7c800124u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu{std::map<uint32_t,uint32_t> m;uint8_t byte=0;uint8_t* get_ptr(uint32_t a){return m.count(a&~3u)?&byte:nullptr;}uint32_t read32(uint32_t a){return m.at(a);}};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=U,ctr=0,msr=0x32,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
struct Prior{bool ok=true;bool restored_sleep_at(Cpu&,bool held)const{return ok&&held;}};
static void trial(unsigned f){
    Cpu c;for(unsigned i=0;i<32;++i)c.gpr[i]=i*17u;c.gpr[1]=0x80050000u;c.gpr[3]=0x90000100u;
    auto original=c.gpr;
    const std::array<ReplyNativeWord,5> words{{{S,S,bl(S,R)},{S,S+4,Nop},{S,S+8,Blr},{R,R,Mtmsr},{R,R+4,Blr}}};
    for(auto w:words)c.mmu.m[w.pc]=w.word;
    c.mmu.m[U]=Nop;
    SleepExitWitness w({S,U,Nop,{R,S+4,bl(S,R),Mtmsr},words});
    if(f==1)c.lr+=4;
    bool ok=w.capture(c,true);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    c.pc=R;c.lr=S+4;c.gpr[1]-=64;c.gpr[3]=0;c.gpr[4]=0x32;c.inst_count+=100;
    ok=w.begin(c,Prior{f!=2},true);if(f==2){assert(!ok&&w.failure()==2);return;}assert(ok);
    if(f==3)c.gpr[4]|=0x8000u;
    c.inst_count+=f==4?2:1;ok=w.before(c,R,Mtmsr,true);
    if(f==3||f==4){assert(!ok&&w.failure()==(f==3?4u:3u));return;}assert(ok);
    if(f==5)c.gpr[3]=1;
    ++c.inst_count;ok=w.before(c,R+4,Blr,true);if(f==5){assert(!ok&&w.failure()==4);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,S+4,Nop,true));
    c.gpr=original;c.lr=U;if(f==6)c.gpr[31]^=1;++c.inst_count;
    ok=w.before(c,S+8,Blr,true);if(f==6){assert(!ok&&w.failure()==5);return;}assert(ok);
    c.pc=U;if(f==7)c.mmu.m[U]=Blr;
    ok=w.poll(c,true);if(f==7){assert(!ok&&w.failure()==6);return;}assert(ok);
    assert(w.returned(c,true)&&w.visits()==4);
    if(f==8){++c.inst_count;assert(!w.returned(c,true));}
}
int main(){for(unsigned f=0;f<=8;++f)trial(f);std::cout<<"V1339_SLEEP_EXIT synthetic=1 valid=1 refused=8 nested_ee_disabled=1 original_execution=0\n";}
