#include "wii_stm_second_v1359.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t S=0x80001000,O=0x80002000,A=0x80003000,P=0x80004000,N=0x60000000;
constexpr uint32_t Store=(36u<<26)|(3u<<21)|(13u<<16),Call=0x48000001u|((O-(S+8))&0x03fffffcu);
struct Mmu {
    std::array<uint8_t,0x6000> a{};
    uint8_t* get_ptr(uint32_t p){return p>=0x80000000u&&p-0x80000000u<a.size()?a.data()+p-0x80000000u:nullptr;}
    uint8_t read8(uint32_t p){return *get_ptr(p);}
    uint32_t read32(uint32_t p){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(p+i);return v;}
    void write32(uint32_t p,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(p+i)=uint8_t(v>>(24u-i*8u));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=S,ctr=0,msr=0x8032,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
struct Prior{bool ok;bool returned(Cpu&,bool h,bool d){return ok&&h&&d;}};
static void trial(unsigned f){
    Cpu c;c.gpr[1]=0x80005000;c.gpr[2]=A-16;c.gpr[13]=A;
    const std::array<ReplyNativeWord,3> words{{{S,S,Store},{S,S+4,N},{S,S+8,Call}}};
    const std::array<StmPath,1> paths{{{P,2}}};const std::array<uint32_t,0> exits{};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    c.mmu.write32(O,N);c.mmu.write32(A,0xffffffffu);
    const std::string_view path="/dev/stm/eventhook";for(unsigned i=0;i<path.size();++i)*c.mmu.get_ptr(P+i)=uint8_t(path[i]);
    Prior prior{f!=1};StmSecondWitness w({S,S+8,O,N,words,exits,paths});
    bool ok=w.begin(c,prior,true,true,1);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    c.inst_count+=f==2?1:2;if(f==3)c.gpr[3]=1;
    ok=w.before(c,S,Store,true,true);if(f==2||f==3){assert(!ok&&w.failure()==(f==2?2u:3u));return;}assert(ok);
    if(f!=4)c.mmu.write32(A,0);
    ++c.inst_count;
    ok=w.before(c,S+4,N,true,true);if(f==4){assert(!ok&&w.failure()==3);return;}assert(ok);
    c.gpr[3]=f==5?P+1:P;if(f==6)c.gpr[4]=1;
    ++c.inst_count;ok=w.before(c,S+8,Call,true,true);if(f==5||f==6){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.pc=O;c.lr=f==7?S+8:S+12;
    ok=w.entry(c,O,true,f!=8);if(f>=7){assert(!ok&&w.failure()==6);return;}assert(ok);
    assert(w.reached(c,true,true)&&w.visits()==3&&w.stores()==1);
    c.mmu.write32(A,1);assert(!w.reached(c,true,true));
}
int main(){for(unsigned f=0;f<9;++f)trial(f);std::cout<<"V1359_SECOND synthetic=1 valid=1 refused=8 original_execution=0\n";}
