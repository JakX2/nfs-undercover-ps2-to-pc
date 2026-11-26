#include "wii_stm_event_return.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,S=B+0x100u,R=B+0x200u,F=B+0x400u,Sp=B+0x600u;
constexpr uint32_t N=0x60000000u,ST=0x908d0000u,BC=0x4182000cu;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=S,lr=S,msr=0x32,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(bool alt,unsigned fault){
    Cpu c;
    std::array<IpcDispatchWord,6> words{{{S,S,BC},{S,S+4,ST},{S,S+8,0x4800000cu},
        {S,S+12,ST},{S,S+16,N},{S,S+20,bl(S+20,R)}}};
    if(fault==2)words[1].word=0x90010000u;
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.gpr[1]=Sp;c.gpr[13]=F;c.gpr[4]=1;
    std::array<StmEventStore,2> sites{{{S+4,F,4,4},{S+12,F,4,4}}};
    if(fault==3)sites[1].address+=4;
    StmEventReturnWitness w({S,S,{S+20,R,bl(S+20,R)},words,sites,{F,8}});
    bool ok=w.begin(c,fault!=1);
    if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,true);};
    c.cr[0].eq=alt;assert(step(S,BC));
    uint32_t site=alt?S+12:S+4;
    if(fault==4)site=alt?S+4:S+12;
    if(fault==5)c.gpr[4]=0;
    ok=step(site,ST);if(fault==4||fault==5){assert(!ok);return;}assert(ok);
    c.mmu.write32(F,fault==6?0u:1u);
    if(fault==7)c.mmu.write32(F+4,1);
    ok=step(site+4,alt?N:0x4800000cu);
    if(fault==6||fault==7){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==8?0u:1u;
    ok=step(S+20,bl(S+20,R));if(fault==8){assert(!ok);return;}assert(ok);
    c.pc=R;c.lr=fault==9?S:S+24;
    ok=w.entry(c,R,true);if(fault==9){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.stores()==1u&&w.flag_preserved(c));
    if(fault==10){c.mmu.write32(F,0);assert(!w.flag_preserved(c));}
}
int main(){for(bool alt:{false,true})for(unsigned f=0;f<=10;++f)trial(alt,f);
    std::cout<<"STM_EVENT_RETURN_TEST cases=22 original_execution=0\n";}
