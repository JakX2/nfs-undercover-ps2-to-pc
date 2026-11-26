#include "wii_ioctl_construction_v1392.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t W=0x80004000u,U=W+0x100u,F=W+0x400u,H=0x90000020u,Q=H+32u,M=0x80005000u,SP=0x80008000u,O=0x80006000u,CB=0x80007000u;
constexpr uint32_t Nop=0x60000000u;
constexpr uint32_t b(uint32_t a,uint32_t t){return 0x48000001u|((t-a)&0x03fffffcu);}
constexpr uint32_t st(unsigned off){return (36u<<26)|(5u<<21)|(6u<<16)|off;}
struct Mmu {
    std::vector<uint8_t> one=std::vector<uint8_t>(0x10000),two=std::vector<uint8_t>(0x1000);
    uint8_t* get_ptr(uint32_t a){if(a>=0x80000000u&&a-0x80000000u<one.size())return one.data()+a-0x80000000u;if(a>=0x90000000u&&a-0x90000000u<two.size())return two.data()+a-0x90000000u;return nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=W,lr=0,ctr=0,msr=0x32,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault,unsigned first,bool input){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=first==2?0:1;c.gpr[4]=StmIos::EventHook;
    c.gpr[5]=input?O+64:0;c.gpr[6]=input?32:0;c.gpr[7]=O;c.gpr[8]=32;c.gpr[9]=CB;
    constexpr uint32_t I=U+32,V=U+36;
    const std::array<unsigned,8> off{0,8,12,16,20,24,28,32};
    const std::array<uint32_t,8> val{StmIos::Ioctl,c.gpr[3],StmIos::EventHook,c.gpr[5]&0x3fffffffu,c.gpr[6],O&0x3fffffffu,32u,CB};
    std::array<ReplyNativeWord,10> words{};
    for(unsigned i=0;i<off.size();++i)words[i]={W,U+4*i,st(off[i])};
    words[8]={W,I,b(I,F)};words[9]={W,V,b(V,F)};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    c.mmu.write32(F,Nop);
    IoctlConstructionWitness w({W,U,{F,I+4,b(I,F),Nop},{F,V+4,b(V,F),Nop},words});
    assert(w.capture(c,true,first));
    c.pc=c.lr=U;c.gpr[1]=SP-64;c.gpr[3]=Q;
    assert(w.begin(c,true,Q,64,{H,256},{M,16}));
    c.gpr[6]=Q;
    for(unsigned i=0;i<off.size();++i){
        c.gpr[5]=val[i];if(fault==1&&i==7)c.gpr[5]=0;
        if(fault==2&&i==3)c.gpr[5]^=1;
        if(fault==3&&i==0)c.gpr[6]=H;
        c.inst_count+=i?1u:2u;
        bool ok=w.before(c,U+4*i,st(off[i]),true);
        if(fault==3&&i==0){assert(!ok);return;}assert(ok);
        c.mmu.write32(Q+off[i],c.gpr[5]);
    }
    // Exercise input first, including its zero-length form. The actual output-first branch is owner-fixture dependent.
    c.gpr[3]=input?O+64:0;c.gpr[4]=input?32:0;
    if(fault==4)c.mmu.write32(H+200,1);
    if(fault==5)c.mmu.write32(M,1);
    if(fault==6)c.mmu.write32(O,1);
    if(fault==7)c.gpr[4]^=1;
    ++c.inst_count;bool ok=w.before(c,I,b(I,F),true);
    if(fault>=1&&fault<=7){assert(!ok);return;}assert(ok);
    c.pc=F;c.lr=fault==8?V+4:I+4;
    ok=w.entry(c,F,true);if(fault==8){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.request_stores()==8&&w.flush_kind()==1);
}
int main(){for(unsigned first:{1u,2u})for(bool input:{false,true})for(unsigned f=0;f<=8;++f)trial(f,first,input);
    std::cout<<"V1392_CONSTRUCTION_TEST cases=36 original_execution=0\n";}
