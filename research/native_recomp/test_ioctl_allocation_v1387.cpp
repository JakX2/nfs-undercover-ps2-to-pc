#include "wii_ioctl_allocation_v1387.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t V=0x80004000u,A=V+0x100u,D=V+0x200u,R=V+0x300u,U=V+0x400u,H=0x90000020u,M=0x80005000u,SP=0x80008000u;
constexpr uint32_t Blr=0x4e800020u,Nop=0x60000000u,Mtmsr=0x7c800124u;
constexpr uint32_t b(uint32_t a,uint32_t t,bool link=false){return 0x48000000u|((t-a)&0x03fffffcu)|unsigned(link);}
constexpr uint32_t St=(36u<<26)|(5u<<21)|(6u<<16),Meta=(36u<<26)|(7u<<21)|(8u<<16);
struct Mmu {
    std::vector<uint8_t> one=std::vector<uint8_t>(0x10000),two=std::vector<uint8_t>(0x1000);
    uint8_t* get_ptr(uint32_t a){if(a>=0x80000000u&&a-0x80000000u<one.size())return one.data()+a-0x80000000u;if(a>=0x90000000u&&a-0x90000000u<two.size())return two.data()+a-0x90000000u;return nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=V,lr=U,ctr=0,msr=0x32,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=2;c.gpr[4]=64;c.gpr[5]=0x12345678;c.gpr[6]=H;c.gpr[7]=H+128;c.gpr[8]=M+12;
    const std::array<ReplyNativeWord,10> words{{{V,V,b(V,A)},{A,A,b(A,D,true)},{A,A+4,St},{A,A+8,Meta},
        {A,A+12,b(A+12,R,true)},{A,A+16,Blr},{D,D,Mtmsr},{D,D+4,Blr},{R,R,Mtmsr},{R,R+4,Blr}}};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    c.mmu.write32(U,Nop);c.mmu.write32(H+128,0xbabe0000u);c.mmu.write32(M+12,H);
    IoctlAllocationWitness w({V,A,U,Nop,{D,A+4,b(A,D,true),Mtmsr},{R,A+16,b(A+12,R,true),Mtmsr},words});
    assert(w.begin(c,true,{H,256},{M+12,4},{M,16}));
    auto step=[&](uint32_t pc,uint32_t op){++c.inst_count;return w.before(c,pc,op,true);};
    assert(step(V,b(V,A)));c.pc=A;assert(w.entry(c,A,true));assert(step(A,b(A,D,true)));
    c.pc=D;c.lr=A+4;assert(w.entry(c,D,true));
    c.gpr[4]=fault==1?0x8032:0x32;
    bool ok=step(D,Mtmsr);if(fault==1){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==2?1u:0u;ok=step(D+4,Blr);if(fault==2){assert(!ok);return;}assert(ok);
    if(fault==3)c.gpr[6]=M;
    ok=step(A+4,St);if(fault==3){assert(!ok);return;}assert(ok);
    c.mmu.write32(H,fault==4?0u:c.gpr[5]);ok=step(A+8,Meta);if(fault==4){assert(!ok);return;}assert(ok);
    c.mmu.write32(M+12,H+128);assert(step(A+12,b(A+12,R,true)));
    c.pc=R;c.lr=A+16;assert(w.entry(c,R,true));c.gpr[4]=0x32;assert(step(R,Mtmsr));c.gpr[3]=0;assert(step(R+4,Blr));
    c.lr=U;c.gpr[3]=fault==5?H+4:H+32;
    if(fault==6)c.gpr[31]=1;
    if(fault==7)c.mmu.write32(H+100,1);
    if(fault==8)c.mmu.write32(SP+8,1);
    ok=step(A+16,Blr);if(fault>=5&&fault<=8){assert(!ok);return;}assert(ok);
    c.pc=U;
    if(fault==9){++c.inst_count;assert(w.inline_return(c,U,Nop,true));}
    else assert(w.poll(c,true));
    assert(w.returned(c,true)&&w.request()==H+32&&w.stores()==2&&w.metadata_stores()==1);
}
int main(){for(unsigned i=0;i<10;++i)trial(i);std::cout<<"V1387_ALLOCATION_TEST cases=10 original_execution=0\n";}
