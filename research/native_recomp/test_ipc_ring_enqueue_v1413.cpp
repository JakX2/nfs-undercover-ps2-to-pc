#include "wii_ipc_ring_enqueue_v1413.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t BASE=0x80000000u,A=BASE+0x100u,R=BASE+0x400u,SP=BASE+0x800u;
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=BASE&&a-BASE<ram.size()?ram.data()+a-BASE:nullptr;}
    uint32_t read32(uint32_t a){auto p=get_ptr(a);assert(p&&get_ptr(a+3u));uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|p[i];return v;}
    void write32(uint32_t a,uint32_t v){auto p=get_ptr(a);assert(p&&get_ptr(a+3u));for(unsigned i=0;i<4;++i)p[i]=uint8_t(v>>(24-8*i));}
};
struct Cpu{Mem mmu;};
static void trial(unsigned n,bool wrap,unsigned fault){
    Cpu c,other;
    const uint32_t old_w=wrap?0xffffffffu:7u,wp=wrap?n-1u:2u;
    const unsigned occ=fault==2?n:1u;
    const uint32_t rp=(wp+n-occ%n)%n;
    c.mmu.write32(A,old_w-occ);c.mmu.write32(A+4,old_w);
    c.mmu.write32(A+8,rp);c.mmu.write32(A+12,fault==3?n:wp);
    if(fault!=4)c.mmu.write32(A+16+4*rp,R+64);
    c.mmu.write32(A+16+4*wp,R+128);
    IpcRingEnqueueWitness w;
    bool ok=w.begin(c,{A,16u+4u*n},{fault==5?A:R,64},{SP,64},fault==5?A:R,n,fault!=1);
    if(fault>=1&&fault<=5){assert(!ok);return;}assert(ok);
    const uint32_t slot=A+16+4*wp;
    if(fault==6)c.mmu.write32(A,0u);
    ok=w.authorize(c,fault==7?A:slot,fault==8?R+32:R,fault==9?2u:4u,fault!=10);
    if(fault>=6&&fault<=10){assert(!ok);return;}assert(ok);
    c.mmu.write32(slot,fault==11?0u:R);
    if(fault==12){assert(!w.authorize(c,slot,R,4,true));return;}
    if(fault==13){assert(!w.settled(other));return;}
    if(fault==14){assert(!w.complete(c));return;}
    ok=w.authorize(c,A+12,fault==15?wp:(wp+1u)%n,4,true);
    if(fault==11||fault==15){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+12,(wp+1u)%n);
    if(fault==16)c.mmu.write32(A+16+4*rp,0u);
    ok=w.authorize(c,A+4,old_w+1u,4,true);
    if(fault==16){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+4,fault==17?old_w:old_w+1u);
    assert(w.complete(c)==(fault!=17));
}
int main(){for(unsigned n:{16u,48u})for(bool wrap:{false,true})for(unsigned f=0;f<=17;++f)trial(n,wrap,f);
    std::cout<<"V1413_RING_TEST cases=72 original_execution=0\n";
}
