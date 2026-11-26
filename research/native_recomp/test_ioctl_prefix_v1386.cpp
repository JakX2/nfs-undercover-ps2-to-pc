#include "wii_stm_ioctl_entry.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t S=0x80004000,D=S+0x100,I=S+0x200,Sp=S+0x300,R13=S+0x400,Out=S+0x500,CB=S+0x600;
constexpr uint32_t Store=(36u<<26)|(3u<<21)|(13u<<16),Mtmsr=0x7c800124u,Blr=0x4e800020u,Nop=0x60000000u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu {
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=S&&a-S<ram.size()?ram.data()+a-S:nullptr;}
    uint32_t read32(uint32_t a){auto p=get_ptr(a);assert(p&&get_ptr(a+3));return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
    void write32(uint32_t a,uint32_t w){auto p=get_ptr(a);assert(p&&get_ptr(a+3));for(unsigned i=0;i<4;++i)p[i]=uint8_t(w>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=S,ctr=0,msr=0x8032,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
#include "wii_ioctl_prefix_v1386.h"
static void prefix_trial(unsigned fault){
    constexpr uint32_t P=S+0x800u,A=S+0x100u,G=S+0x200u;
    constexpr uint32_t frame=(37u<<26)|(1u<<21)|(1u<<16)|0xffc0u;
    constexpr uint32_t st=(36u<<26)|(31u<<21)|(11u<<16)|0xfffcu;
    const std::array<ReplyNativeWord,7> words{{{S,S,frame},{S,S+4,bl(S+4,G)},
        {S,S+8,Nop},{S,S+12,bl(S+12,A)},{G,G,st},{G,G+4,Blr},{A,A,Nop}}};
    Cpu c;c.msr=0x32;c.gpr[1]=P;c.gpr[11]=P;c.gpr[31]=0x12345678;c.gpr[2]=R13;c.gpr[13]=R13;
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    IoctlPrefixWitness w({S,S+4,G,S+12,A,1,words});
    assert(w.begin(c,true));
    if(fault==1)c.msr|=0x8000;
    ++c.inst_count;bool ok=w.before(c,S,frame,true);
    if(fault==1){assert(!ok);return;}assert(ok);
    c.gpr[1]=P-64;c.mmu.write32(P-64,fault==2?0u:P);
    ++c.inst_count;ok=w.before(c,S+4,bl(S+4,G),true);
    if(fault==2){assert(!ok);return;}assert(ok);
    c.pc=G;c.lr=fault==3?S+12:S+8;
    ok=w.entry(c,G,true);if(fault==3){assert(!ok);return;}assert(ok);
    if(fault==4)c.gpr[31]^=1;
    ++c.inst_count;ok=w.before(c,G,st,true);
    if(fault==4){assert(!ok);return;}assert(ok);
    c.mmu.write32(P-4,fault==5?0u:c.gpr[31]);
    ++c.inst_count;ok=w.before(c,G+4,Blr,true);
    if(fault==5){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.before(c,S+8,Nop,fault!=6);
    if(fault==6){assert(!ok);return;}assert(ok);
    c.gpr[4]=fault==7?0u:64u;
    ++c.inst_count;assert(w.before(c,S+12,bl(S+12,A),true));
    c.pc=A;c.lr=S+16;
    ok=w.entry(c,A,true);if(fault==7){assert(!ok);return;}assert(ok);
    assert(w.reached(c,true)&&w.saved()==1&&w.stores()==2&&w.visits()==6);
    if(fault==8){c.mmu.write32(P-8,5);assert(!w.reached(c,true));}
}
int main(){for(unsigned i=0;i<9;++i)prefix_trial(i);
    std::cout<<"V1386_PREFIX_TEST cases=9 original_execution=0\n";
}
