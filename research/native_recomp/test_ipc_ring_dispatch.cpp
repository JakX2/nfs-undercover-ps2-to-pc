#include "wii_ipc_ring_dispatch.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,A=B+0x100u,Credit=B+0x300u,Req=B+0x400u,Sp=B+0x600u;
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cpu{Mem mmu;};
static void trial(unsigned n,bool wrap,unsigned fault){
    Cpu c,other;
    const uint32_t rp=wrap?n-1u:1u,r=wrap?0xffffffffu:5u,wp=(rp+1u)%n;
    const uint32_t slot=A+16u+4u*rp;
    c.mmu.write32(A,r);c.mmu.write32(A+4,fault==2?r+2u:r+1u);
    c.mmu.write32(A+8,rp);c.mmu.write32(A+12,fault==3?rp:wp);
    c.mmu.write32(slot,fault==4?Req+32:Req);c.mmu.write32(Credit,fault==5?0u:1u);
    IpcRingDispatchWitness w;
    bool ok=w.begin(c,{A,16u+4u*n},{fault==6?A:Credit,4},{Req,64},{Sp,64},n,fault!=1);
    if(fault>=1&&fault<=6){assert(!ok);return;}assert(ok);
    if(fault==7){assert(!w.authorize(c,A,r+1u,4,true));return;}
    if(fault==8)c.mmu.write32(Req,1);
    ok=w.message_written(c,fault==9?Req:Req&0x3fffffffu,fault!=10);
    if(fault>=8&&fault<=10){assert(!ok);return;}assert(ok);
    if(fault==11){assert(!w.control_written(c,true));return;}
    if(fault==12){assert(!w.settled(other));return;}
    ok=w.authorize(c,fault==13?slot:A+8,fault==14?rp:wp,fault==15?2u:4u,fault!=16);
    if(fault>=13&&fault<=16){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+8,fault==17?rp:wp);
    if(fault==18){assert(!w.authorize(c,A+8,wp,4,true));return;}
    ok=w.authorize(c,A,r+1u,4,true);
    if(fault==17){assert(!ok);return;}assert(ok);c.mmu.write32(A,r+1u);
    if(fault==19)c.mmu.write32(A+16u+4u*((rp+1u)%n),Req+64u);
    ok=w.authorize(c,Credit,fault==20?1u:0u,4,true);
    if(fault==19||fault==20){assert(!ok);return;}assert(ok);
    c.mmu.write32(Credit,fault==21?1u:0u);
    if(fault==22)c.mmu.write32(Req+60,1u);
    ok=w.control_written(c,fault!=23);
    if(fault>=21&&fault<=23){assert(!ok);return;}assert(ok);
    if(fault==24)c.mmu.write32(slot,0u);
    assert(w.complete(c)==(fault!=24));
    assert(w.stores()==3);
}
int main(){
    for(unsigned n:{16u,48u})for(bool wrap:{false,true})for(unsigned f=0;f<=24;++f)trial(n,wrap,f);
    std::cout<<"IPC_RING_DISPATCH_TEST cases=100 original_execution=0\n";
}
