#include "wii_register_continuation.h"
#include "wii_post_stm_sc_leaf_shadow.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,T=B+0x200u,U=B+0x300u,L=B+0x400u,A=B+0x500u,SP=B+0xc00u,N=0x60000000u;
constexpr uint32_t S=R+20u;
constexpr uint32_t ins(unsigned op,unsigned r,unsigned a,int v){return (op<<26)|(r<<21)|(a<<16)|(uint32_t(v)&0xffffu);}
constexpr uint32_t bl(uint32_t a,uint32_t z){return 0x48000001u|((z-a)&0x03fffffcu);}
struct Mem {
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu {
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=L,ctr=0,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.gpr[14]=0x1234;
    *c.mmu.get_ptr(A)=0x5a;
    const std::array<IpcDispatchWord,5> prefix{{{R,R,ins(37,1,1,-64)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,68)},{R,R+12,ins(36,14,1,60)},{R,R+16,bl(R+16,T)}}};
    const std::array<ScFormatterAccess,3> access{{{R,4,-64,true,true},{R+8,4,4,true,true},{R+12,4,-4,true,true}}};
    const std::array<StmFinalSlot,2> slots{{{4,32},{-4,14}}};
    const std::array<IpcDispatchWord,2> leaf{{{T,T,ins(34,3,3,0)},{T,T+4,0x4e800020}}};
    const std::array<uint32_t,2> active{{T,T+4}};
    const std::array<ScLeafAccess,1> reads{{{T,0,1,false}}};
    const std::array<IpcDispatchWord,3> resume{{{R,S,ins(14,14,3,1)},{R,S+4,ins(14,4,14,0)},{R,S+8,bl(S+8,U)}}};
    for(auto x:prefix)c.mmu.write32(x.pc,x.word);
    for(auto x:leaf)c.mmu.write32(x.pc,x.word);
    for(auto x:resume)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(U,N);
    ScFormatterWitness formatter({R,L,T,leaf[0].word,64,prefix,access,slots});
    assert(formatter.begin(c,true)&&formatter.poll(c,true));++c.inst_count;assert(formatter.entry(c,R,true));
    for(unsigned i=0;i<prefix.size();++i){
        auto x=prefix[i];++c.inst_count;assert(formatter.before(c,x.pc,x.word,true));
        if(i==0){c.gpr[1]=SP-64;c.mmu.write32(SP-64,SP);}
        if(i==1)c.gpr[0]=L;
        if(i==2)c.mmu.write32(SP+4,L);
        if(i==3)c.mmu.write32(SP-4,c.gpr[14]);
        if(i==4){c.pc=T;c.lr=S;}
    }
    assert(formatter.entry(c,T,true)&&formatter.reached(c,true));
    ScLeafShadow shadow({T,S,resume[0].word,leaf,reads,0,0,0,active,true,0x5au});
    auto frame=[&](){return formatter.frame_held(c,true);};
    assert(shadow.begin(c,{A,1},frame())&&shadow.poll(c,frame()));++c.inst_count;assert(shadow.entry(c,T,frame()));
    ++c.inst_count;assert(shadow.before(c,T,leaf[0].word,frame()));c.gpr[3]=0x5a;
    ++c.inst_count;assert(shadow.before(c,T+4,leaf[1].word,frame()));c.pc=S;
    assert(shadow.poll(c,frame())&&shadow.reached(c,frame()));
    bool device_held=true;
    auto held=[&](){return formatter.frame_held(c,shadow.object_held(c,device_held));};
    if(fault==1)c.mmu.write32(SP-4,0);
    if(fault==2)*c.mmu.get_ptr(A)=0;
    if(fault==3)c.lr+=4;
    RegisterContinuationWitness next({R,S,U,N,1u<<14,resume});
    bool ok=next.begin(c,held());
    if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok);
    assert(next.poll(c,held()));++c.inst_count;assert(next.entry(c,S,held()));
    for(unsigned i=0;i<resume.size();++i){
        auto x=resume[i];++c.inst_count;ok=next.before(c,x.pc,x.word,held());
        if(i==1&&(fault==4||fault==5||fault==6)){assert(!ok);return;}assert(ok);
        if(i==0){
            c.gpr[14]=fault==4?0x5cu:0x5bu;
            if(fault==5)c.mmu.write32(SP+4,0);
            if(fault==6)device_held=false;
        }
        if(i==1)c.gpr[4]=c.gpr[14];
        if(i==2){c.pc=fault==7?U+4:U;c.lr=S+12;}
    }
    if(fault==8)*c.mmu.get_ptr(A)=0;
    ok=next.entry(c,c.pc,held());
    if(fault==7||fault==8){assert(!ok);return;}assert(ok);
    assert(next.reached(c,held())&&formatter.visits()==5&&shadow.visits()==2&&next.visits()==3);
    assert(c.gpr[3]==0x5a&&c.gpr[4]==0x5b&&c.gpr[14]==0x5b&&c.mmu.read32(SP-4)==0x1234);
}
int main(){for(unsigned i=0;i<=8;++i)trial(i);std::cout<<"REGISTER_CONTINUATION_JOIN_TEST cases=9 original_execution=0\n";}
