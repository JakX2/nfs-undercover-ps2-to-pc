#include "wii_ipc_dispatch_execution.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,S=B+0x100u,W=B+0x200u,R=B+0x300u,
    Ring=B+0x400u,Credit=B+0x500u,Req=B+0x600u,Sp=B+0x700u,P=B+0x800u,A=B+0x900u,F=B+0xa00u;
constexpr uint32_t ST=0x90830000u,LD=0x80630000u,Ret=0x4e800020u,N=0x60000000u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=S,lr=S,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault){
    Cpu c;
    const std::array<IpcDispatchWord,12> words{{
        {S,S,N},{S,S+4,bl(S+4,W)},{S,S+8,ST},{S,S+12,ST},{S,S+16,ST},
        {S,S+20,bl(S+20,R)},{S,S+24,bl(S+24,W)},{S,S+28,N},
        {W,W,ST},{W,W+4,Ret},{R,R,LD},{R,R+4,Ret}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Ring+4,1);c.mmu.write32(Ring+12,1);c.mmu.write32(Ring+16,Req);c.mmu.write32(Credit,1);
    c.gpr[1]=Sp;
    IpcDispatchExecution w({S,S,S+28,{{{S+4,W,bl(S+4,W)},{S+20,R,bl(S+20,R)},{S+24,W,bl(S+24,W)}}},
        words,{Ring,80},{Credit,4},16,{{P,4},{P+4,4},{A,8},{F,8}}});
    bool ok=w.begin(c,fault!=1,{Req,64},{Sp,64});
    if(fault==1){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t ins){++c.inst_count;return w.before(c,pc,ins,true);};
    if(fault==2)c.mmu.write32(A,1);
    ok=step(S,N);if(fault==2){assert(!ok);return;}assert(ok);
    assert(step(S+4,bl(S+4,W)));c.pc=W;c.lr=fault==3?S:S+8;
    ok=w.entry(c,W,true);if(fault==3){assert(!ok);return;}assert(ok);
    c.gpr[3]=0xcd000000u;c.gpr[4]=Req&0x3fffffffu;
    assert(step(W,ST));
    ok=w.write_allowed(c,fault==4?0xcd000004u:c.gpr[3],fault==5?Req:c.gpr[4],true);
    if(fault==4||fault==5){assert(!ok);return;}assert(ok);
    assert(w.write_done(c,c.gpr[3],c.gpr[4],true));
    if(fault==6)c.gpr[31]=1;
    ok=step(W+4,Ret);if(fault==6){assert(!ok);return;}assert(ok);
    c.pc=S+8;assert(w.returned(c,c.pc,true));
    for(unsigned i=0;i<3;++i){
        c.gpr[3]=i==0?Ring+8:i==1?Ring:Credit;c.gpr[4]=i==2?0u:1u;
        if(fault==7&&i==0)c.gpr[3]=Ring+12;
        ok=step(S+8+4*i,ST);if(fault==7&&i==0){assert(!ok);return;}assert(ok);
        c.mmu.write32(c.gpr[3],fault==8&&i==0?0u:c.gpr[4]);
        if(fault==8&&i==1){assert(false);}
        if(fault==8&&i==0){assert(!step(S+12,ST));return;}
    }
    assert(step(S+20,bl(S+20,R)));c.pc=R;c.lr=S+24;assert(w.entry(c,R,true));
    c.gpr[3]=0xcd000004u;assert(step(R,LD));
    if(fault==9){assert(!w.read_allowed(c,0xcd000000u,true));return;}
    assert(w.read_allowed(c,c.gpr[3],true));assert(w.read_done(c,0x30u,true));
    c.gpr[3]=fault==10?0u:0x30u;
    ok=step(R+4,Ret);if(fault==10){assert(!ok);return;}assert(ok);
    c.pc=S+24;assert(w.returned(c,c.pc,true));
    assert(step(S+24,bl(S+24,W)));c.pc=W;c.lr=S+28;assert(w.entry(c,W,true));
    c.gpr[3]=0xcd000004u;c.gpr[4]=0x31u;assert(step(W,ST));
    assert(w.write_allowed(c,c.gpr[3],c.gpr[4],true));
    assert(w.write_done(c,c.gpr[3],c.gpr[4],true));
    assert(step(W+4,Ret));c.pc=S+28;
    if(fault==11)c.mmu.write32(Req,1);
    ok=w.returned(c,c.pc,true);if(fault==11){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.stores()==3&&w.writes()==2&&w.reads()==1&&w.calls()==3);
    if(fault==12){c.mmu.write32(F,1);assert(!w.reached(c,true));}
}
int main(){for(unsigned f=0;f<=12;++f)trial(f);
    std::cout<<"IPC_DISPATCH_EXECUTION_TEST cases=13 original_execution=0\n";}
