#include "wii_cooperative_context_v1306.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t T=0x80010000u,Save=0x80020000u,Ret=0x80030000u,Load=0x80040000u,Rfi=Load+0xd4u;
constexpr uint32_t Active=0x800000d4u,Phys=0x800000c0u,Current=0x800000e4u;
struct Mmu{
    std::map<uint32_t,uint32_t> w;uint8_t byte=0;
    uint8_t* get_ptr(uint32_t a){return w.count(a&~3u)?&byte:nullptr;}
    uint32_t read32(uint32_t a){return w.at(a);}
    uint16_t read16(uint32_t a){return uint16_t(read32(a&~3u)>>(a&2u?0:16));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};
    uint32_t pc=Save,lr=Ret,ctr=123u,xer=0x80000000u,msr=0x32u,srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100;
    bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;auto& m=c.mmu.w;
    for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+i;
    c.gpr[1]=0x80050000u;c.gpr[3]=T;c.cr[3].eq=true;
    const auto gp=c.gpr;const auto lr=c.lr,ctr=c.ctr,xer=c.xer,msr=c.msr;
    for(unsigned i=0;i<0x2ccu;i+=4)m[T+i]=0;
    m[c.gpr[1]]=0;m[c.gpr[1]+4]=0;m[Active]=m[Current]=T;m[Phys]=T&0x3fffffffu;
    m[Rfi]=0x4c000064u;
    CooperativeContextWitness w({T,Save,Ret,Load,Rfi,Active,Phys,Current,0xffffffffu});
    if(fault==1)c.gpr[3]+=4;
    bool ok=w.capture(c,true);
    if(fault==1){assert(!ok&&w.failure()==1u);return;}assert(ok);
    for(unsigned i=0;i<32;++i)m[T+4*i]=gp[i];
    m[T+12]=1;m[T+128]=0x00020000u;m[T+132]=lr;m[T+136]=ctr;m[T+140]=xer;
    m[T+408]=lr;m[T+412]=msr;c.pc=Ret;c.gpr[3]=0;c.inst_count+=32;
    if(fault==2)m[T+31*4]^=1;
    if(fault==3)m[T+12]=0;
    if(fault==4)m[T+408]+=4;
    if(fault==5)m[T+0x1a0]=2;
    if(fault==6)c.gpr[13]^=1;
    if(fault==17)m.erase(T+0x200u);
    ok=w.saved(c,true);
    if((fault>=2&&fault<=6)||fault==17){assert(!ok&&w.failure()==2u);return;}assert(ok);
    m[Active]=T+0x1000u;++c.inst_count;
    if(fault==7)m[T+0x2c4]^=1;
    if(fault==7){assert(!w.preserved(c,true));return;}
    assert(w.preserved(c,true));
    c.pc=Load;c.gpr[3]=T;m[Active]=m[Current]=T;m[Phys]=T&0x3fffffffu;m[T+0x2c8]=2u<<16;++c.inst_count;
    if(fault==8)m[Current]+=4;
    if(fault==9)m[T+0x2c8]=1u<<16;
    if(fault==18)m.erase(T+0x2c8u);
    ok=w.loader_entry(c,true);
    if(fault==8||fault==9||fault==18){assert(!ok&&w.failure()==3u);return;}assert(ok);
    c.gpr=gp;c.gpr[3]=1;c.gpr[5]^=1; // volatile r5 is not a cooperative ABI guarantee
    c.pc=Rfi;c.srr0=Ret;c.srr1=msr;c.inst_count+=40;
    if(fault==10)c.gpr[3]=0;
    if(fault==11)c.gpr[31]^=1;
    if(fault==12)c.srr0+=4;
    if(fault==13)c.cr[3].eq=false;
    ok=w.before_rfi(c,Rfi,m[Rfi],true);
    if(fault>=10&&fault<=13){assert(!ok&&w.failure()==4u);return;}assert(ok);
    c.pc=Ret;c.msr=msr;
    if(fault==14)++c.inst_count;
    if(fault==15)c.msr|=0x8000u;
    if(fault==16)c.gpr[1]+=8;
    ok=w.returned(c,true);
    if(fault>=14){assert(!ok&&w.failure()==5u);return;}
    assert(ok&&w.stage()==5u);
}
int main(){
    for(unsigned f=0;f<=18;++f)trial(f);
    std::cout<<"V1306_COOPERATIVE_CONTEXT synthetic=1 valid=1 refused=18 saved_abi=1 resume_abi=1 original_execution=0\n";
}
