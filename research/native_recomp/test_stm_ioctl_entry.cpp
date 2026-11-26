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
struct Prior{bool returned(Cpu&,bool h,bool d){return h&&d;}};
static void trial(unsigned first,unsigned f){
    Cpu c;c.gpr[1]=Sp;c.gpr[13]=R13;c.gpr[2]=R13+32;c.gpr[3]=1;
    const std::array<ReplyNativeWord,7> words{{{S,S,Store},{S,S+4,bl(S+4,D)},{S,S+8,Nop},{S,S+12,bl(S+12,I)},
        {D,D,Mtmsr},{D,D+4,Blr},{I,I,Nop}}};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    const std::array<uint32_t,1> stores{S};const std::array<AllocatorRange,1> text{{{CB,4u}}};
    StmIoctlEntryWitness w({S,S,S+12,{D,S+8,bl(S+4,D),Mtmsr},{I,S+16,bl(S+12,I),Nop},words,stores,text});
    Prior p;
    bool ok=w.begin(c,p,true,f!=1,first);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    assert(w.poll(c,true));if(f==2){assert(!w.poll(c,true)&&w.failure()==6);return;}
    c.inst_count+=f==3?1u:2u;ok=w.before(c,S,Store,true);if(f==3){assert(!ok&&w.failure()==2);return;}assert(ok);
    c.mmu.write32(R13,f==4?0u:1u);++c.inst_count;ok=w.before(c,S+4,bl(S+4,D),true);
    if(f==4){assert(!ok&&w.failure()==2);return;}assert(ok);
    c.pc=D;c.lr=f==5?S+12:S+8;ok=w.entry(c,D,true);if(f==5){assert(!ok&&w.failure()==5);return;}assert(ok);
    c.gpr[4]=f==6?0x8032u:0x32u;++c.inst_count;ok=w.before(c,D,Mtmsr,true);
    if(f==6){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.msr=f==7?0x8032u:0x32u;c.gpr[3]=f==8?0u:1u;++c.inst_count;
    ok=w.before(c,D+4,Blr,true);if(f==7||f==8){assert(!ok&&w.failure()==(f==7?2u:4u));return;}assert(ok);
    c.pc=S+8;++c.inst_count;assert(w.before(c,S+8,Nop,true));
    c.gpr[3]=(first==2?0u:1u)^(f==9?1u:0u);c.gpr[4]=f==10?1u:StmIos::EventHook;
    c.gpr[5]=0;c.gpr[6]=0;c.gpr[7]=Out;c.gpr[8]=f==11?0u:32u;c.gpr[9]=f==12?CB+4u:CB;
    if(f==13)c.mmu.write32(R13,0u);
    ++c.inst_count;ok=w.before(c,S+12,bl(S+12,I),true);
    if(f>=9&&f<=13){assert(!ok&&w.failure()==(f==13?2u:4u));return;}assert(ok);
    c.pc=I;c.lr=S+16;ok=w.entry(c,I,f!=14);
    if(f==14){assert(!ok&&w.failure()==5);return;}assert(ok);
    assert(w.reached(c,true)&&w.stores()==1u&&w.visits()==6u&&w.expected_msr()==0x32u);
    if(f==15){c.gpr[8]=0;assert(!w.reached(c,true));}
}
int main(){for(unsigned first:{1u,2u})for(unsigned f=0;f<=15;++f)trial(first,f);
    std::cout<<"V1382_STM_IOCTL_ENTRY synthetic=1 cases=32 both_orders=1 native_disable_contract=1 original_execution=0\n";}
