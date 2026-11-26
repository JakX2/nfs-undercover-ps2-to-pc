#include "wii_ipc_deferred_ack_memory.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,Ring=B+0x100u,Credit=B+0x300u,P=B+0x400u,U=P+4u,
    A=B+0x500u,F=B+0x600u,Req=B+0x700u,Sp=B+0x800u;
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cpu{Mem mmu;};
static void trial(unsigned fd,bool wrap,unsigned fault){
    Cpu c,other;
    const uint32_t rp=wrap?0u:3u,rc=wrap?0u:7u;
    c.mmu.write32(Ring,rc);c.mmu.write32(Ring+4,fault==2?rc+1u:rc);
    c.mmu.write32(Ring+8,rp);c.mmu.write32(Ring+12,rp);
    c.mmu.write32(Ring+16u+4u*((rp+15u)%16u),Req);
    c.mmu.write32(Credit,fault==3?1u:0u);
    c.mmu.write32(P,2);c.mmu.write32(U,fault==4?0u:1u);
    c.mmu.write32(A+8,Req);c.mmu.write32(F+8,fault==5?1u-fd:fd);
    if(fault==6){c.mmu.write32(A+12,Req);c.mmu.write32(F+12,fd);}
    c.mmu.write32(Req+8,fd);
    IpcDeferredAckMemory w;
    bool ok=w.begin(c,{Ring,80},{Credit,4},{{P,4},{U,4},{A,128},{F,128}},{Req,64},{Sp,64},16,fd,fault!=1);
    if(fault>=1&&fault<=6){assert(!ok);return;}assert(ok);
    if(fault==7){assert(!w.authorize(c,Credit,1,4,true));return;}
    if(fault==8){assert(!w.latch_cleared(c,false));return;}
    if(fault==9){assert(!w.settled(other));return;}
    assert(w.latch_cleared(c,true));
    if(fault==10)c.mmu.write32(A+8,0);
    ok=w.authorize(c,fault==11?U:Credit,fault==12?0u:1u,fault==13?2u:4u,fault!=14);
    if(fault>=10&&fault<=14){assert(!ok);return;}assert(ok);
    c.mmu.write32(Credit,fault==15?0u:1u);
    if(fault==16){assert(!w.complete(c,true));return;}
    ok=w.authorize(c,fault==17?P:U,fault==18?1u:0u,4,true);
    if(fault==15||fault==17||fault==18){assert(!ok);return;}assert(ok);
    c.mmu.write32(U,fault==19?1u:0u);
    if(fault==20)c.mmu.write32(Req,1);
    ok=w.complete(c,fault!=21);
    if(fault>=19&&fault<=21){assert(!ok);return;}assert(ok);
    assert(w.preserved(c)&&w.stores()==2u&&c.mmu.read32(P)==2u&&c.mmu.read32(A+8)==Req);
    if(fault==22){c.mmu.write32(F+8,0xffffffffu);assert(!w.preserved(c));}
}
int main(){for(unsigned fd:{0u,1u})for(bool wrap:{false,true})for(unsigned f=0;f<=22;++f)trial(fd,wrap,f);
    std::cout<<"IPC_DEFERRED_ACK_MEMORY_TEST cases=92 original_execution=0\n";}
