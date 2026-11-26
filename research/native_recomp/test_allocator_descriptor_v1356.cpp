#include "wii_allocator_descriptor_v1356.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t T=0x80000100u,H=0x90000100u;
struct Mmu{
    std::array<uint8_t,4096> a{},b{};
    uint8_t* get_ptr(uint32_t p){if(p>=0x80000000u&&p-0x80000000u<a.size())return a.data()+p-0x80000000u;if(p>=0x90000000u&&p-0x90000000u<b.size())return b.data()+p-0x90000000u;return nullptr;}
    uint32_t read32(uint32_t p){uint32_t v=0;for(unsigned i=0;i<4;++i){auto q=get_ptr(p+i);assert(q);v=(v<<8)|*q;}return v;}
    void write32(uint32_t p,uint32_t v){for(unsigned i=0;i<4;++i){auto q=get_ptr(p+i);assert(q);*q=uint8_t(v>>(24u-8u*i));}}
};
struct Cpu{Mmu mmu;};
static void trial(unsigned f){
    Cpu c;AllocatorDescriptorWitness w;AllocatorRange heap{H,256};
    std::array<AllocatorRange,2> tables{{{T,128},{f==1?T:T+128,128}}};
    constexpr uint32_t R=T+32;
    if(f==2)c.mmu.write32(R,H);
    bool ok=w.before_create(c,tables);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    auto record=[&](uint32_t a){c.mmu.write32(a,H);c.mmu.write32(a+4,7);c.mmu.write32(a+8,256);c.mmu.write32(a+12,H+32);};
    record(R);if(f==3)record(T+128);c.mmu.write32(H+32,f==4?0xbabe0001u:0xbabe0000u);
    ok=w.after_create(c,heap);if(f>=2&&f<=4){assert(!ok&&w.failure()==2);return;}assert(ok);
    assert(w.field().base==R+12&&w.field().size==4&&w.guard().base==R&&w.guard().size==16);
    if(f==6)c.mmu.write32(R+4,8);
    ok=w.release_entry(c,heap,f==5?3u:2u);if(f==5||f==6){assert(!ok&&w.failure()==3);return;}assert(ok);
    c.mmu.write32(R+12,H+64);c.mmu.write32(H+64,f==8?0xbabe0001u:0xbabe0000u);
    if(f==9)c.mmu.write32(R+8,128);
    ok=w.returned(c,f==7?0u:1u);if(f>=7&&f<=9){assert(!ok&&w.failure()==4);return;}assert(ok);
#ifdef UNDERCOVER_TEST_SECOND_RETURN
    if(f>=10u){
        c.mmu.write32(R+12,H+96);c.mmu.write32(H+96,0xbabe0000u);
        if(f==12)c.mmu.write32(R+4,8);
        ok=w.second_release_entry(c,heap,f==11?3u:2u);
        if(f==11||f==12){assert(!ok&&w.failure()==5);return;}assert(ok);
        if(f==13){assert(!w.second_release_entry(c,heap,2u));return;}
        if(f==14)c.mmu.write32(R+12,H+100);
        ok=w.second_returned(c,f==15?0u:1u);
        if(f==14||f==15){assert(!ok&&!w.second_completed());return;}assert(ok&&w.second_completed());
    }
#endif
}
int main(){for(unsigned f=0;f<10;++f)trial(f);
#ifdef UNDERCOVER_TEST_SECOND_RETURN
for(unsigned f=10;f<=15;++f){trial(f);}
std::cout<<"V1375_SECOND_DESCRIPTOR cases=6\n";
#endif
std::cout<<"V1356_DESCRIPTOR synthetic=1 valid=1 refused=9 exact_field=1 original_execution=0\n";}
