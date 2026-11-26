#include "wii_register_continuation.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,S=R+16u,T=B+0x400u,N=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned r,unsigned a,int v){return (op<<26)|(r<<21)|(a<<16)|(uint32_t(v)&0xffffu);}
constexpr uint32_t bl(uint32_t a,uint32_t z){return 0x48000001u|((z-a)&0x03fffffcu);}
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|*get_ptr(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=S,lr=S,ctr=0,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void direct(unsigned fault){
    Cpu c;c.gpr[1]=B+0x900;c.gpr[3]=3;c.gpr[14]=42;
    const std::array<IpcDispatchWord,4> path{{{R,S,ins(14,fault==6?1:14,3,7)},
        {R,S+4,ins(14,4,14,2)},{R,S+8,fault==7?ins(36,4,1,0):ins(11,0,4,12)},{R,S+12,bl(S+12,T)}}};
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(T,N);
    if(fault==1)c.lr+=4;
    if(fault==2)c.mmu.write32(S,N);
    RegisterContinuationWitness w({R,S,T,N,fault==5?0u:1u<<14,path});
    bool ok=w.begin(c,fault!=3);if(fault>=1&&fault<=3){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,S,true));
    for(unsigned i=0;i<path.size();++i){
        auto x=path[i];++c.inst_count;ok=w.before(c,x.pc,x.word,fault!=4);
        if((i==0&&fault>=4&&fault<=6)||(i==2&&(fault==7||fault==8))||(i==3&&fault==9)){assert(!ok);return;}
        assert(ok);
        if(i==0)c.gpr[14]=10;
        if(i==1)c.gpr[4]=fault==8?13:12;
        if(i==2)c.cr[0].eq=fault!=9;
        if(i==3){c.pc=fault==10?T+4:T;c.lr=S+16;}
    }
    if(fault==11)c.gqr[4]=1;
    if(fault==12)c.gpr[1]+=4;
    ok=w.entry(c,c.pc,true);if(fault>=10&&fault<=12){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.visits()==4&&w.polls()==0&&c.gpr[14]==10&&c.gpr[4]==12);
    assert(!w.reached(c,false));
}
static void backedge(unsigned fault){
    Cpu c;c.gpr[1]=B+0x900;c.ctr=2;
    const uint32_t back=0x42000000u|((S-(S+4))&0xfffcu);
    const std::array<IpcDispatchWord,5> path{{{R,S,ins(14,3,3,1)},{R,S+4,back},
        {R,S,ins(14,3,3,1)},{R,S+4,back},{R,S+8,bl(S+8,T)}}};
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(T,N);
    RegisterContinuationWitness w({R,S,T,N,0,path});
    assert(w.begin(c,true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,S,true));
    for(unsigned i=0;i<path.size();++i){
        const auto x=path[i];++c.inst_count;bool ok=w.before(c,x.pc,x.word,true);
        if(fault==1&&i==2){assert(!ok);return;}assert(ok);
        if(x.pc==S)++c.gpr[3];
        else if(x.pc==S+4){
            c.pc=fault==2?S:S+4;
            if(fault==3)--c.ctr;
            if(fault!=1){ok=w.poll(c,fault!=4);if(fault>=2&&fault<=4){assert(!ok);return;}assert(ok);}
            if(fault==5){assert(!w.poll(c,true));return;}--c.ctr;
        }else{c.pc=T;c.lr=S+12;}
    }
    assert(w.entry(c,T,true)&&w.reached(c,true)&&w.visits()==5&&w.polls()==2&&c.ctr==0&&c.gpr[3]==2);
}
int main(){for(unsigned i=0;i<=12;++i)direct(i);for(unsigned i=0;i<=5;++i)backedge(i);
    std::cout<<"REGISTER_CONTINUATION_TEST cases=19 original_execution=0\n";}
