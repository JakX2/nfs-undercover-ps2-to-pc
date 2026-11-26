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
static void trial(unsigned fault,unsigned first,bool input,bool output_first){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=first==2?0:1;c.gpr[4]=StmIos::EventHook;
    c.gpr[5]=input?O+64:0;c.gpr[6]=input?32:0;c.gpr[7]=O;c.gpr[8]=32;c.gpr[9]=CB;
    constexpr uint32_t J=U+36,I=J+4,V=I+4;
    const uint32_t local_store=(36u<<26)|(5u<<21)|(1u<<16)|(fault==10?64u:16u);
    // The branch target is outside the observed corridor in the two
    // escape tests. The exact branch word remains authenticated.
    const bool escape=fault==12||fault==13;
    const uint32_t jump=escape?0x41820100u:b(J,output_first?V:I)&~1u;
    const std::array<unsigned,8> off{0,8,12,16,20,24,28,32};
    const std::array<uint32_t,8> val{StmIos::Ioctl,c.gpr[3],StmIos::EventHook,c.gpr[5]&0x3fffffffu,c.gpr[6],O&0x3fffffffu,32u,CB};
    std::array<ReplyNativeWord,12> words{};
    words[0]={W,U,local_store};
    for(unsigned i=0;i<off.size();++i)words[i+1]={W,U+4*(i+1),st(off[i])};
    words[9]={W,J,jump};words[10]={W,I,b(I,F)};words[11]={W,V,b(V,F)};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    c.mmu.write32(F,Nop);
    IoctlConstructionWitness w({W,U,{F,I+4,b(I,F),Nop},{F,V+4,b(V,F),Nop},words});
    assert(w.capture(c,true,first));
    c.pc=c.lr=U;c.gpr[1]=SP-64;c.gpr[3]=Q;
    assert(w.begin(c,true,Q,64,{H,256},{M,16}));
    c.gpr[6]=Q;
    c.gpr[5]=0x12345678u;c.inst_count+=2u;
    if(fault==9)c.gpr[1]+=64u;
    bool local_ok=w.before(c,U,local_store,true);
    if(fault==9){assert(!local_ok);return;}
    if(fault==10){assert(!local_ok&&w.base_class()==1&&w.range_failure()==7);return;}assert(local_ok);
    c.mmu.write32(c.gpr[1]+16u,c.gpr[5]^(fault==11?1u:0u));
    for(unsigned i=0;i<off.size();++i){
        c.gpr[5]=val[i];if(fault==1&&i==7)c.gpr[5]=0;
        if(fault==2&&i==3)c.gpr[5]^=1;
        if(fault==3&&i==0)c.gpr[6]=H;
        ++c.inst_count;
        bool ok=w.before(c,U+4*(i+1),st(off[i]),true);
        if((fault==3||fault==11)&&i==0){assert(!ok);return;}assert(ok);
        c.mmu.write32(Q+off[i],c.gpr[5]);
    }
    // Exercise both authenticated first-flush choices, and refuse a
    // nonempty input that would otherwise be skipped by output-first.
    ++c.inst_count;
    if(fault==13)c.cr[0].eq=true;
    const bool branch_ok=w.before(c,J,jump,true);
    if(fault==13){assert(!branch_ok&&w.control_failure()==8);return;}
    assert(branch_ok);
    const uint32_t site=output_first?V:I;
    c.gpr[3]=output_first?O:input?O+64:0;c.gpr[4]=output_first||input?32:0;
    if(fault==4)c.mmu.write32(H+200,1);
    if(fault==5)c.mmu.write32(M,1);
    if(fault==6)c.mmu.write32(O,1);
    if(fault==7)c.gpr[4]^=1;
    ++c.inst_count;bool ok=w.before(c,site,b(site,F),true);
    if((fault>=1&&fault<=7)||(output_first&&input)){assert(!ok);return;}assert(ok);
    c.pc=F;c.lr=fault==8?(output_first?I:V)+4:site+4;
    ok=w.entry(c,F,true);if(fault==8){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.request_stores()==8&&w.flush_kind()==(output_first?2u:1u));
    // The new submit frame may move SP and initialize an extension word.
    // The old whole-allocation guard is retired only after this handoff.
    c.gpr[1]-=32;c.mmu.write32(Q+48,0x13572468u);
    assert(w.identity_preserved(c,true)&&!w.preserved(c,true));
    c.mmu.write32(H+200,1);assert(!w.identity_preserved(c,true));c.mmu.write32(H+200,0);
    c.mmu.write32(O,1);assert(!w.identity_preserved(c,true));c.mmu.write32(O,0);
    assert(w.identity_preserved(c,true));
    c.mmu.write32(Q+32,0);c.mmu.write32(Q+36,CB);
    assert(!w.identity_preserved(c,true)&&w.wire_failure()==8);
}
int main(){for(unsigned first:{1u,2u}){
    for(unsigned f=0;f<=11;++f){trial(f,first,false,false);trial(f,first,true,false);trial(f,first,false,true);}
    trial(0,first,true,true);
    trial(12,first,true,false);trial(13,first,true,false);
    }
    std::cout<<"V1392_CONSTRUCTION_TEST cases=78 original_execution=0\n";}
