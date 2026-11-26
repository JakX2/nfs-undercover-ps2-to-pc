#include "wii_open_return_v1351.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t T=0x80010000u,O=T+0x100u,S=T+0x200u,Nop=0x60000000u,Blr=0x4e800020u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu{std::map<uint32_t,uint32_t> m;uint8_t byte=0;uint8_t* get_ptr(uint32_t a){return m.count(a&~3u)?&byte:nullptr;}uint32_t read32(uint32_t a){return m.at(a);}};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=O,lr=T+4,ctr=0,msr=0x8032,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
struct Prior{bool ok=true,inlined=false;bool returned(Cpu&,bool held){return ok&&held;}bool inline_completed()const{return ok&&inlined;}};
static void trial(unsigned f,uint32_t fd=0){
    Cpu c;c.gpr[1]=0x80050000;c.gpr[2]=0x80060000;c.gpr[13]=0x80070000;
    const std::array<ReplyNativeWord,6> words{{{O,O,bl(O,S)},{O,O+4,Nop},{O,O+8,Blr},{S,S,Nop},{S,S+4,Nop},{S,S+8,Blr}}};
    for(auto w:words)c.mmu.m[w.pc]=w.word;
    c.mmu.m[T]=bl(T,O);c.mmu.m[T+4]=Nop;
    OpenReturnWitness w({O,S,S+4,O+4,T+4,bl(T,O),bl(O,S),Nop,words});
    auto o=c.gpr;
    if(f==1)c.lr=T+8;
    bool ok=w.capture_open(c,true);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    c.pc=S;c.lr=O+4;c.gpr[1]-=64;c.gpr[31]=5;c.inst_count+=10;auto s=c.gpr;
    if(f==2)c.lr=O+8;
    ok=w.capture_submit(c,true);if(f==2){assert(!ok&&w.failure()==2);return;}assert(ok);
    c.pc=S+4;c.gpr[1]-=64;c.inst_count+=100;Prior prior{f!=3,f==12u||f==14u};
    ok=f>=12u?w.begin_inline(c,prior,true,true,fd):w.begin(c,prior,true,f!=4,fd);
    if(f==3||f==4||f==13){assert(!ok&&w.failure()==3);return;}assert(ok);
    c.inst_count+=f>=12u?(f==14u?1u:0u):2u;
    ok=w.before(c,S+4,Nop,true,true);
    if(f==14u){assert(!ok&&w.failure()==4);return;}assert(ok);c.gpr=s;c.lr=O+4;
    if(f==5)c.gpr[31]^=1;
    c.gpr[3]=fd^(f==6?1u:0u);
    ++c.inst_count;ok=w.before(c,S+8,Blr,true,true);
    if(f==5||f==6){assert(!ok&&w.failure()==5);return;}assert(ok);
    c.pc=O+4;if(f==7)c.pc+=4;
    ok=w.poll(c,true,true);if(f==7){assert(!ok&&w.failure()==6);return;}assert(ok);
    c.inst_count+=f==8?1:2;ok=w.before(c,O+4,Nop,true,true);
    if(f==8){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.gpr=o;c.gpr[3]=fd;c.lr=T+4;if(f==9)c.gpr[13]^=1;++c.inst_count;
    ok=w.before(c,O+8,Blr,true,true);if(f==9){assert(!ok&&w.failure()==5);return;}assert(ok);
    c.pc=T+4;ok=w.poll(c,true,f!=10);if(f==10){assert(!ok&&w.failure()==6);return;}assert(ok);
    assert(w.returned(c,true,true)&&w.visits()==4);
    if(f==11){++c.inst_count;assert(!w.returned(c,true,true));}
}
int main(){for(unsigned f=0;f<=14;++f)trial(f);
#ifdef UNDERCOVER_TEST_SECOND_RETURN
for(unsigned f=0;f<=14;++f)trial(f,1u);std::cout<<"V1375_SECOND_OPEN_RETURN cases=15\n";
#endif
std::cout<<"V1353_OPEN_RETURN synthetic=1 valid=2 refused=13 two_abi=1 descriptor=1 inline_handoff=1 original_execution=0\n";}
