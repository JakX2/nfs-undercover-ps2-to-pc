#include "wii_ipc_profile_execution.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,H=B+0x100u,C=B+0x200u,Req=B+0x400u,Sp=B+0x500u,
    Ring=B+0x600u,P=B+0x700u,U=P+4u,A=B+0x800u,F=B+0x900u;
constexpr uint32_t BL=0x48000001u|((H-C)&0x03fffffcu),N=0x60000000u,Ret=0x4e800020u,
    Ctr=0x7c0903a6u,Loop=0x4200fffcu,BeqRet=0x4d820020u,
    S1=0x90a60000u,S2=0x90a60004u,S3=0x90670000u,S4=0x7c88392eu;
struct Mem {
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=H,lr=C+4,msr=0x32,ctr=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(bool available,unsigned fault){
    Cpu c;
    const uint32_t badop=fault==20?0x7c0803a6u:N;
    const std::array<IpcProfileNativeWord,9> words{{{H,S1},{H+4,S2},{H+8,Ctr},{H+12,badop},
        {H+16,Loop},{H+20,BeqRet},{H+24,S3},{H+28,S4},{H+32,Ret}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(C,BL);c.mmu.write32(C+4,N);c.mmu.write32(Req+8,1);
    c.gpr[1]=Sp;c.gpr[3]=Req;c.gpr[4]=1;c.gpr[5]=1;c.gpr[6]=P;c.gpr[7]=A;c.gpr[8]=F-A;
    c.gpr[0]=2;c.gpr[31]=17;
    c.mmu.write32(F,available?0xffffffffu:0u);
    c.mmu.write32(F+4,0u);
    IpcProfileExecutionWitness w({H,C,BL,N,words,{{P,4},{U,4},{A,8},{F,8}}});
    if(fault==1)c.lr=C+8;
    if(fault==2)c.gpr[3]=Req+32;
    if(fault==3)c.gpr[4]=0;
    if(fault==4)c.mmu.write32(C+4,0);
    bool ok=w.begin(c,true,{Req,64},{Sp,64},{Ring,80},1);
    if(fault>=1&&fault<=4){assert(!ok);return;}assert(ok);
    auto step=[&](uint32_t pc,uint32_t word){++c.inst_count;return w.before(c,pc,word,true);};
    if(fault==5)c.msr|=0x8000u;
    if(fault==6)c.gpr[5]=2;
    if(fault==7)c.mmu.write32(Ring,1);
    if(fault==8)++c.inst_count;
    ok=step(H,S1);if(fault>=5&&fault<=8){assert(!ok);return;}assert(ok);
    c.mmu.write32(P,fault==9?0u:1u);
    ok=step(H+4,S2);if(fault==9){assert(!ok);return;}assert(ok);c.mmu.write32(U,1);
    assert(step(H+8,Ctr));c.ctr=fault==10?1:2;
    ok=step(H+12,badop);if(fault==10||fault==20){assert(!ok);return;}assert(ok);
    assert(step(H+16,Loop));c.pc=H+16;
    ok=w.poll(c,true);assert(ok);
    if(fault==11){assert(!w.poll(c,true));return;}
    --c.ctr;
    ok=step(fault==12?H+20:H+12,badop);
    if(fault==12){assert(!ok);return;}assert(ok);
    assert(step(H+16,Loop));c.pc=H+16;assert(w.poll(c,true));--c.ctr;
    c.cr[0].eq=!available;
    if(fault==13)c.gpr[31]=0;
    ok=step(H+20,BeqRet);
    if(!available&&fault==13){assert(!ok);return;}assert(ok);
    if(available){
        if(fault==14)c.mmu.write32(Req,1);
        ok=step(H+24,S3);if(fault==14){assert(!ok);return;}assert(ok);c.mmu.write32(A,Req);
        // stwx r4,r8,r7: effective address F.
        ok=step(H+28,S4);assert(ok);c.mmu.write32(F,fault==15?0u:1u);
        if(fault==16)c.mmu.write32(Sp,1);
        ok=step(H+32,Ret);if(fault==13||fault==15||fault==16){assert(!ok);return;}assert(ok);
    }
    c.pc=fault==17?C+8:C+4;
    if(fault==18)c.lr=C+8;
    if(fault==19)c.mmu.write32(Ring,2);
    ok=w.returned(c,c.pc,true);
    if(fault>=17&&fault<=19){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.stores()==(available?4u:2u)&&w.polls()==2u);
}
int main(){
    for(bool available:{false,true})for(unsigned f=0;f<=20;++f)trial(available,f);
    std::cout<<"IPC_PROFILE_EXECUTION_TEST cases=42 original_execution=0\n";
}
