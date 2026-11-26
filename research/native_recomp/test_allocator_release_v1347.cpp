#include "wii_allocator_release_v1347.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace undercover::wii;
constexpr uint32_t F=0x80004000u,D=F+0x100u,R=F+0x200u,U=F+0x300u,Q=0x90000040u,H=0x90000020u,
 Nop=0x60000000u,Blr=0x4e800020u,Mtmsr=0x7c800124u,Store=(36u<<26)|(5u<<21)|(6u<<16);
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu{
    std::vector<uint8_t> one=std::vector<uint8_t>(0x10000),two=std::vector<uint8_t>(0x1000);
    uint8_t* get_ptr(uint32_t a){if(a>=0x80000000u&&a-0x80000000u<one.size())return one.data()+a-0x80000000u;if(a>=0x90000000u&&a-0x90000000u<two.size())return two.data()+a-0x90000000u;return nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){auto p=get_ptr(a);assert(p&&get_ptr(a+3));return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
    void write32(uint32_t a,uint32_t w){auto p=get_ptr(a);assert(p&&get_ptr(a+3));for(unsigned i=0;i<4;++i)p[i]=uint8_t(w>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=F,lr=U,ctr=0,msr=0x8032,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
struct Prior{bool ok=true;bool release_at(Cpu&,bool held)const{return ok&&held;}};
static void trial(unsigned f){
    Cpu c;c.gpr[1]=0x80008000u;c.gpr[4]=Q;c.gpr[5]=0x12345678;c.gpr[6]=H;
    const std::array<ReplyNativeWord,8> words{{{F,F,bl(F,D)},{F,F+4,Store},{F,F+8,bl(F+8,R)},{F,F+12,Blr},
        {D,D,Mtmsr},{D,D+4,Blr},{R,R,Mtmsr},{R,R+4,Blr}}};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    c.mmu.write32(U,Nop);c.mmu.write32(Q,StmIos::Reply);c.mmu.write32(Q+8,StmIos::Open);
    AllocatorReleaseWitness w({F,U,Nop,{D,F+4,bl(F,D),Mtmsr},{R,F+12,bl(F+8,R),Mtmsr},words});
    bool ok=w.begin(c,Prior{f!=1},true,{H,256},Q);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t v){++c.inst_count;return w.before(c,pc,v,true);};
    assert(step(F,bl(F,D)));c.pc=D;c.lr=F+4;assert(w.entry(c,D,true));
    c.gpr[4]=f==2?0x8032:0x32;ok=step(D,Mtmsr);if(f==2){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.msr=0x32;c.gpr[3]=1;assert(step(D+4,Blr));
    if(f==3)c.gpr[6]=0x80000000u;
    ok=step(F+4,Store);if(f==3){assert(!ok&&w.failure()==3&&w.store_failure()==5);return;}assert(ok);
    c.mmu.write32(H,f==4?0:c.gpr[5]);ok=step(F+8,bl(F+8,R));
    if(f==4){assert(!ok&&w.failure()==3&&w.store_failure()==3);return;}assert(ok);
    c.pc=R;c.lr=F+12;assert(w.entry(c,R,true));c.gpr[4]=0x8032;assert(step(R,Mtmsr));
    c.msr=0x8032;c.pc=R+4;ok=w.poll(c,f!=5);if(f==5){assert(!ok&&w.failure()==7);return;}assert(ok);
    assert(step(R+4,Blr));c.lr=U;if(f==6)c.gpr[31]=1;
    ok=step(F+12,Blr);if(f==6){assert(!ok&&w.failure()==5);return;}assert(ok);
    c.pc=U;if(f==7)c.mmu.write32(U,Blr);
    ok=w.poll(c,true);if(f==7){assert(!ok&&w.failure()==7);return;}assert(ok);
    assert(w.returned(c,true)&&w.heap_stores()==1&&w.visits()==8);
    if(f==8){++c.inst_count;assert(!w.returned(c,true));}
}
int main(){for(unsigned f=0;f<=8;++f)trial(f);std::cout<<"V1347_ALLOCATOR_RELEASE synthetic=1 valid=1 refused=8 exact_store=1 restored_abi=1 original_execution=0\n";}
