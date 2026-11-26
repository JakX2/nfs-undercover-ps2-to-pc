#include "wii_ipc_profile_enqueue_v1415.h"
#include <array>
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t Base=0x80000000u,P=Base+0x100u,U=P+4u,A=Base+0x200u,F=Base+0x300u,
    R=Base+0x400u,Sp=Base+0x500u,Ring=Base+0x600u;
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=Base&&a-Base<ram.size()?ram.data()+a-Base:nullptr;}
    uint32_t read32(uint32_t a){auto p=get_ptr(a);assert(p&&get_ptr(a+3u));uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|p[i];return v;}
    void write32(uint32_t a,uint32_t v){auto p=get_ptr(a);assert(p&&get_ptr(a+3u));for(unsigned i=0;i<4;++i)p[i]=uint8_t(v>>(24-8*i));}
};
struct Cpu{Mem mmu;};
static void trial(unsigned fd,bool available,bool wrap,unsigned fault){
    Cpu c,other;
    const uint32_t prior=wrap?0xffffffffu:5u;
    c.mmu.write32(P,prior);c.mmu.write32(U,prior);
    for(unsigned i=0;i<32;++i){c.mmu.write32(A+4*i,R+64u);c.mmu.write32(F+4*i,fd);}
    // Half-free pairs are not eligible. The first complete free pair
    // must be chosen even when a later one is also free.
    c.mmu.write32(A,0u);c.mmu.write32(F+4u,0xffffffffu);
    if(available){for(unsigned i:{2u,7u}){c.mmu.write32(A+4*i,0);c.mmu.write32(F+4*i,0xffffffffu);}}
    IpcProfileEnqueueWitness w;
    IpcProfileLayout layout{{P,4},{fault==2?P:U,4},{A,128},{F,fault==3?124u:128u}};
    bool ok=w.begin(c,layout,{fault==4?A:R,64},{Sp,64},{Ring,80},fault==5?2u:fd,fault!=1);
    if(fault>=1&&fault<=5){assert(!ok);return;}assert(ok&&w.slot_available()==available);
    if(fault==6)c.mmu.write32(A+12,0);
    ok=w.authorize(c,P,fault==7?prior:prior+1u,fault==8?2u:4u,fault!=9);
    if(fault>=6&&fault<=9){assert(!ok);return;}assert(ok);
    c.mmu.write32(P,fault==10?prior:prior+1u);
    if(fault==11){assert(!w.authorize(c,P,prior+1u,4,true));return;}
    if(fault==12){assert(!w.settled(other));return;}
    ok=w.authorize(c,U,prior+1u,4,true);
    if(fault==10){assert(!ok);return;}assert(ok);
    c.mmu.write32(U,prior+1u);
    if(!available){
        if(fault==13){assert(!w.authorize(c,A+8,R,4,true));return;}
        if(fault==14)c.mmu.write32(F+12,0xffffffffu);
        assert(w.complete(c)==(fault!=14));return;
    }
    if(fault==13){assert(!w.complete(c));return;}
    ok=w.authorize(c,fault==14?A+28:A+8,R,4,true);
    if(fault==14){assert(!ok);return;}assert(ok);c.mmu.write32(A+8,R);
    ok=w.authorize(c,F+8,fault==15?1u-fd:fd,4,true);
    if(fault==15){assert(!ok);return;}assert(ok);c.mmu.write32(F+8,fd);
    if(fault==16)c.mmu.write32(A+28,R);
    assert(w.complete(c)==(fault!=16));
}
int main(){for(unsigned fd:{0u,1u})for(bool available:{false,true})for(bool wrap:{false,true})
    for(unsigned f=0;f<=16;++f)trial(fd,available,wrap,f);
    std::cout<<"V1415_PROFILE_TEST cases=136 original_execution=0\n";
}
