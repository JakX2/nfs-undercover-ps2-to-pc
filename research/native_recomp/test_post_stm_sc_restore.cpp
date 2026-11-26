#include "wii_post_stm_sc_restore.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,C=B+0x200u,Sp=B+0x600u,Nop=0x60000000u;
constexpr uint32_t MF=0x7c0000a6u,MT=0x7c000124u,ORI=0x60008000u,ISYNC=0x4c00012cu,BLR=0x4e800020u;
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|*get_ptr(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=C,msr=0x32,ctr=1,xer=0,srr0=B+0x300u,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=fault==2?0u:1u;
    std::array<IpcDispatchWord,5> words{{{R,R,MF},{R,R+4,fault==7?Nop:ORI},{R,R+8,MT},{R,R+12,ISYNC},{R,R+16,BLR}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(C,Nop);
    ScQuietRestoreWitness w({R,C,Nop,R+8,R+12,ISYNC,words});
    bool ok=w.begin(c,fault!=1);if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    if(fault==3)++c.inst_count;
    ok=w.poll(c,true);if(fault==3){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==4?R+4:R,true);
    if(fault==4){assert(!ok);return;}assert(ok);
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,fault==5&&i==0?Nop:words[i].word,true);};
    ok=step(0);if(fault==5){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==6?0:c.msr;
    ok=step(1);if(fault==6){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==7?0x32u:0x8032u;
    ok=step(2);if(fault==7){assert(!ok);return;}assert(ok);
    c.msr=fault==8?0x32u:0x8032u;c.pc=fault==9?R+16:R+12;
    if(fault==10)c.gqr[4]^=1;
    ok=w.poll(c,fault!=11);if(fault>=8&&fault<=11){assert(!ok);return;}assert(ok&&w.enabled(c,true));
    if(fault==12)++c.inst_count;
    ok=w.poll(c,true);if(fault==12){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==13?R:R+12,true);
    if(fault==13){assert(!ok);return;}assert(ok);
    if(fault==14)c.srr0^=4;
    ok=step(3);if(fault==14){assert(!ok);return;}assert(ok);
    if(fault==15)c.gpr[31]^=1;
    ok=step(4);if(fault==15){assert(!ok);return;}assert(ok);
    c.pc=fault==16?C+4:C;
    ok=w.poll(c,true);if(fault==16){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==5&&w.expected_msr()==0x8032u);
    if(fault==17){++c.inst_count;assert(!w.reached(c,true));}
}
int main(){for(unsigned i=0;i<=17;++i)trial(i);std::cout<<"POST_STM_SC_RESTORE_TEST cases=18 original_execution=0\n";}
