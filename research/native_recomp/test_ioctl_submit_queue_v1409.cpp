#include "wii_ioctl_submit_queue_v1409.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t S=0x80001000u,D=0x80002000u,Q=0x80003000u,SP=0x80008000u,R=0x90000100u;
constexpr uint32_t N=0x60000000u,Mt=0x7c800124u,Blr=0x4e800020u,St=0x90610008u,ReqSt=0x90650004u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{
    std::vector<uint8_t> one=std::vector<uint8_t>(0x10000),two=std::vector<uint8_t>(0x1000);
    uint8_t* get_ptr(uint32_t a){if(a>=0x80000000u&&a-0x80000000u<one.size())return one.data()+a-0x80000000u;if(a>=0x90000000u&&a-0x90000000u<two.size())return two.data()+a-0x90000000u;return nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mem mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=S,msr=0x32,ctr=0,dispatch_saved_ctx=0;
 uint64_t inst_count=100;bool is_running=true,in_callback=false;};
static void trial(unsigned fault,bool alias){
    Cpu c;c.gpr[1]=SP;c.gpr[4]=c.msr;c.gpr[5]=R;c.gpr[31]=0x12345678;
    const uint32_t st=fault==9?ReqSt:St;
    const uint32_t branch=0x41820008u;
    std::array<ReplyNativeWord,7> words{{{S,S,bl(S,D)},{S,S+4,branch},{S,S+8,st},{S,S+12,bl(S+12,Q)},{D,D,Mt},{D,D+4,N},{D,D+8,Blr}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Q,N);
    IoctlSubmitQueueWitness w({S,{D,S+4,bl(S,D),Mt},{Q,S+16,bl(S+12,Q),N},words});
    if(fault==1)c.msr|=0x8000u;
    bool ok=w.begin(c,true,R,64,fault==2?SP:SP+64);
    if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,S,bl(S,D),true));
    c.pc=D;c.lr=fault==3?S+8:S+4;
    ok=w.entry(c,D,true);if(fault==3){assert(!ok);return;}assert(ok);
    if(fault==4)c.gpr[4]|=0x8000u;
    ++c.inst_count;ok=w.before(c,D,Mt,true);if(fault==4){assert(!ok);return;}assert(ok);
    c.pc=fault==5?D:D+4;ok=w.poll(c,true);if(fault==5){assert(!ok);return;}assert(ok);
    if(fault==6){assert(!w.poll(c,true));return;}
    ++c.inst_count;assert(w.before(c,D+4,N,true));c.gpr[3]=fault==7?1u:0u;
    if(fault==8)c.gpr[31]^=1u;
    ++c.inst_count;ok=w.before(c,D+8,Blr,true);
    if(fault==7||fault==8){assert(!ok);return;}assert(ok);
    c.cr[0].eq=alias&&fault!=9&&fault!=10;
    ++c.inst_count;assert(w.before(c,S+4,branch,true));
    if(!c.cr[0].eq){
        ++c.inst_count;ok=w.before(c,S+8,st,true);
        if(fault==9){assert(!ok&&w.destination_class()==2u&&w.value_class()==1u&&w.store_form()==1u);return;}assert(ok);
        c.mmu.write32(SP+8,fault==10?1u:0u);
    }
    if(fault==11)c.mmu.write32(R,1u);
    c.gpr[3]=fault==12?R+32u:alias?(R&0x3fffffffu):R;
    ++c.inst_count;ok=w.before(c,S+12,bl(S+12,Q),true);
    if(fault>=10&&fault<=12){assert(!ok);return;}assert(ok);
    c.pc=Q;c.lr=fault==13?S+4:S+16;
    ok=w.entry(c,Q,fault!=14);if(fault==13||fault==14){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.polls()==1&&w.stores()==unsigned(!alias));
    if(fault==15){c.mmu.write32(R+60,1u);assert(!w.reached(c,true));}
}
static void ring_trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[4]=c.msr;
    constexpr uint32_t A=0x80006000u,Slot=A+16u+4u*2u;
    constexpr uint32_t StReq=0x90650000u,StPtr=0x90e6000cu,StCount=0x91060004u;
    const std::array<uint32_t,3> sites{S+4,S+8,fault==1?S+8:S+12};
    const std::array<ReplyNativeWord,8> words{{{S,S,bl(S,D)},{S,S+4,StReq},{S,S+8,StPtr},{S,S+12,StCount},
        {S,S+16,bl(S+16,Q)},{D,D,Mt},{D,D+4,N},{D,D+8,Blr}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Q,N);c.mmu.write32(A,2);c.mmu.write32(A+4,2);
    c.mmu.write32(A+8,2);c.mmu.write32(A+12,2);
    IoctlSubmitQueueWitness w({S,{D,S+4,bl(S,D),Mt},{Q,S+20,bl(S+16,Q),N},words,{A,80},16,sites});
    bool ok=w.begin(c,true,R,64,SP+64);if(fault==1){assert(!ok);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,S,bl(S,D),true));
    c.pc=D;c.lr=S+4;assert(w.entry(c,D,true));
    ++c.inst_count;assert(w.before(c,D,Mt,true));c.pc=D+4;assert(w.poll(c,true));
    ++c.inst_count;assert(w.before(c,D+4,N,true));c.gpr[3]=0;
    ++c.inst_count;assert(w.before(c,D+8,Blr,true));
    c.gpr[3]=fault==2?R+32:R;c.gpr[5]=fault==3?Slot+4:Slot;c.gpr[6]=A;c.gpr[7]=3;c.gpr[8]=3;
    if(fault==4)c.mmu.write32(A+8,3);
    ++c.inst_count;ok=w.before(c,S+4,StReq,true);if(fault>=2&&fault<=4){assert(!ok);return;}assert(ok);
    c.mmu.write32(Slot,fault==5?0:R);
    ++c.inst_count;ok=w.before(c,S+8,StPtr,true);if(fault==5){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+12,3);
    if(fault==6)c.gpr[8]=4;
    ++c.inst_count;ok=w.before(c,S+12,StCount,true);if(fault==6){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+4,3);
    if(fault==7)c.mmu.write32(R,1);
    ++c.inst_count;ok=w.before(c,S+16,bl(S+16,Q),true);if(fault==7){assert(!ok);return;}assert(ok);
    c.pc=Q;c.lr=S+20;assert(w.entry(c,Q,true)&&w.reached(c,true)&&w.ring_stores()==3&&w.stores()==3);
    if(fault==8){c.mmu.write32(A,3);assert(!w.reached(c,true));}
}
int main(){for(bool alias:{false,true})for(unsigned f=0;f<=15;++f)trial(f,alias);
    for(unsigned f=0;f<=8;++f)ring_trial(f);
    std::cout<<"V1409_SUBMIT_QUEUE_TEST cases=41 original_execution=0\n";}
