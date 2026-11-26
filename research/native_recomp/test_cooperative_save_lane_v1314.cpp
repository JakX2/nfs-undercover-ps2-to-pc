#include "wii_cooperative_save_lane_v1314.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t T=0x80010000u,Save=0x80020000u,Ret=0x80030000u,Load=0x80040000u,Rfi=Load+0xd4u;
constexpr uint32_t Active=0x800000d4u,Phys=0x800000c0u,Current=0x800000e4u,Nop=0x60000000u,Blr=0x4e800020u;
struct Mmu{
    std::map<uint32_t,uint32_t> w;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return w.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return w.at(a);}
    uint16_t read16(uint32_t a){return uint16_t(read32(a&~3u)>>(a&2u?0:16));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};std::array<uint32_t,8> gqr{};
    uint32_t pc=Save,lr=Ret,ctr=123u,xer=0x80000000u,msr=0x32u,srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;auto& m=c.mmu.w;std::array<uint32_t,3> words{Nop,Nop,Blr};
    for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+i;
    for(unsigned i=0;i<8;++i)c.gqr[i]=0x100u+i;
    c.gpr[1]=0x80050000u;c.gpr[3]=T;c.cr[3].eq=true;
    auto gp=c.gpr;
    for(unsigned i=0;i<0x2ccu;i+=4)m[T+i]=0;
    m[c.gpr[1]]=0;m[c.gpr[1]+4]=0;m[Active]=m[Current]=T;m[Phys]=T&0x3fffffffu;
    for(unsigned i=0;i<words.size();++i)m[Save+4u*i]=words[i];
    m[Ret]=Nop;
    CooperativeSaveLane w({{T,Save,Ret,Load,Rfi,Active,Phys,Current,0xffffffffu},words,Nop,0xfeu});
    if(fault==1)m[Save+4u]=0;
    bool ok=w.capture(c,true);if(fault==1){assert(!ok&&w.failure()==1u);return;}assert(ok);
    ++c.inst_count;if(fault==2)++c.inst_count;
    ok=w.before(c,fault==3?Save+4u:Save,Nop,true);
    if(fault==2||fault==3){assert(!ok&&w.failure()==3u);return;}assert(ok);
    ++c.inst_count;if(fault==4)c.gqr[1]^=1;
    ok=w.before(c,Save+4u,Nop,true);if(fault==4){assert(!ok&&w.failure()==3u);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,Save+8u,Blr,true));
    // Synthetic stores model the separate actual native save operation.
    for(unsigned i=0;i<32;++i)m[T+4u*i]=gp[i];
    m[T+12u]=1;m[T+128u]=0x00020000u;m[T+132u]=c.lr;m[T+136u]=c.ctr;m[T+140u]=c.xer;
    m[T+408u]=c.lr;m[T+412u]=c.msr;
    for(unsigned i=1;i<8;++i)m[T+0x1a4u+4u*i]=c.gqr[i];
    c.pc=Ret;c.gpr[3]=0;++c.inst_count;
    if(fault==5)m[T+0x1a8u]^=1;
    if(fault==6)c.gpr[3]=1;
    if(fault==7)m[Ret]=Blr;
    ok=w.before(c,Ret,Nop,true);
    if(fault==5){assert(!ok&&w.failure()==5u);return;}
    if(fault==6||fault==7){assert(!ok&&w.failure()==4u);return;}
    assert(ok&&w.stage()==2u&&w.visits()==3u&&w.preserved(c,true));
    if(fault==8){m[T+0x2c4u]^=1;assert(!w.preserved(c,true));}
}
int main(){
    for(unsigned i=0;i<=8;++i)trial(i);
    std::cout<<"V1314_SAVE_LANE synthetic=1 valid=1 refused=8 gqr=1 exact_ticks=1 original_execution=0\n";
}
