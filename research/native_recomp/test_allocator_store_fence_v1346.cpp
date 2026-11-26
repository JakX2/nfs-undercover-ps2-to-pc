#include "wii_allocator_store_fence_v1346.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace undercover::wii;
constexpr uint32_t S=0x80004000u,H=0x90000020u,M=0x80006000u;
constexpr uint32_t d(unsigned op,unsigned rs,unsigned ra,int imm){return op<<26|rs<<21|ra<<16|(unsigned(imm)&0xffffu);}
constexpr uint32_t x(unsigned xo,unsigned rs,unsigned ra,unsigned rb){return 31u<<26|rs<<21|ra<<16|rb<<11|xo<<1;}
struct Mmu{
    std::vector<uint8_t> a=std::vector<uint8_t>(0x10000),b=std::vector<uint8_t>(0x1000);
    uint8_t* get_ptr(uint32_t p){if(p>=0x80000000u&&p-0x80000000u<a.size())return a.data()+p-0x80000000u;if(p>=0x90000000u&&p-0x90000000u<b.size())return b.data()+p-0x90000000u;return nullptr;}
    uint8_t read8(uint32_t p){auto q=get_ptr(p);assert(q);return *q;}
    void write(uint32_t p,uint32_t v,unsigned n=4){for(unsigned i=0;i<n;++i){auto q=get_ptr(p+i);assert(q);*q=uint8_t(v>>(8*(n-i-1)));}}
};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};};
static void trial(unsigned f){
    Cpu c;c.gpr[1]=S+128;c.gpr[4]=0x12345678;c.gpr[5]=H;c.gpr[6]=4;c.gpr[13]=M;
    AllocatorStoreFence w;
    bool ok=w.begin(c,{S,136},{H,256},f==1?AllocatorRange{H+32,4}:AllocatorRange{M,16});
    if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    assert(w.before(c,d(37,1,1,-32)));c.mmu.write(S+96,S+128);
    if(f!=2)c.gpr[1]=S+96;
    ok=w.settled(c);if(f==2){assert(!ok&&w.failure()==3);return;}assert(ok);
    if(f==3)c.gpr[5]=H+254;
    if(f==4)c.gpr[5]=0xcd006400u;
    ok=w.before(c,d(36,4,5,0));if(f==3||f==4){assert(!ok&&w.failure()==5&&w.range_failure()==(f==3?2u:3u)&&w.base_class()==3u);return;}assert(ok);
    c.mmu.write(H,f==5?0x12345679:0x12345678);
    ok=w.settled(c);if(f==5){assert(!ok&&w.failure()==3);return;}assert(ok);
    if(f==6){assert(!w.before(c,d(54,4,5,0))&&w.failure()==4);return;}
    assert(w.before(c,x(407,4,5,6)));c.mmu.write(H+4,0x5678,2);assert(w.settled(c));
    c.gpr[30]=0x11223344;c.gpr[31]=0x55667788;
    assert(w.before(c,d(47,30,5,8)));c.mmu.write(H+8,c.gpr[30]);c.mmu.write(H+12,c.gpr[31]);assert(w.settled(c));
    assert(w.before(c,d(36,4,13,0)));c.mmu.write(M,c.gpr[4]);
    if(f==7)c.mmu.write(H+256,1,1);
    if(f==8)c.mmu.write(H+40,1,1);
    if(f==9)c.mmu.write(H+4,0x1234,2);
    ok=w.finished(c);
    if(f>=7){assert(!ok&&w.failure()==(f==7?2u:6u));return;}
    assert(ok);
    assert(w.stores()==5&&w.stack_stores()==1&&w.heap_stores()==3&&w.metadata_stores()==1);
}
static void range_trial(unsigned f){
    Cpu c;c.gpr[1]=S+128;c.gpr[4]=0x12345678;c.gpr[5]=H;c.gpr[6]=4;c.gpr[13]=M;
    AllocatorStoreFence w;assert(w.begin(c,{S,134},{H,258},{M,6}));
    unsigned expect=0;uint32_t addr=0;
    switch(f){
        case 0:addr=0xffffffffu;expect=1;break;
        case 1:addr=H+1;expect=2;break;
        case 2:addr=0xcd006400u;expect=3;break;
        case 3:addr=S+132;expect=4;break;
        case 4:addr=H+256;expect=5;break;
        case 5:addr=M+4;expect=6;break;
        case 6:addr=M+32;expect=7;break;
        case 7:addr=H+512;expect=8;break;
        default:assert(false);
    }
    c.gpr[5]=addr;
    assert(!w.before(c,d(36,4,5,0))&&w.failure()==5&&w.range_failure()==expect&&w.base_class()==3u);
    assert(!w.stores()&&!w.heap_stores());
}
int main(){for(unsigned f=0;f<8;++f)range_trial(f);for(unsigned f=0;f<=9;++f)trial(f);Cpu c;AllocatorStoreFence empty;assert(empty.begin(c,{S,136},{H,256}));assert(!empty.finished(c));std::cout<<"V1354_ALLOCATOR_STORE_FENCE synthetic=1 valid=1 refused=18 exact_bytes=1 complete_heap_shadow=1 range_diagnostics=8 original_execution=0\n";}
