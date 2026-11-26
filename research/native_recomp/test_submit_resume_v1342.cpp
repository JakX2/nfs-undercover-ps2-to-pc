#include "wii_submit_resume_v1342.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace undercover::wii;
constexpr uint32_t S=0x80004000u,R=S+0x100u,F=S+0x200u,O=S+0x300u,Q=0x90000020u,Nop=0x60000000u,Blr=0x4e800020u,Mtmsr=0x7c800124u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mmu{
    std::vector<uint8_t> one=std::vector<uint8_t>(0x10000),two=std::vector<uint8_t>(0x100);
    uint8_t* get_ptr(uint32_t a){if(a>=0x80000000u&&a-0x80000000u<one.size())return one.data()+a-0x80000000u;if(a>=0x90000000u&&a-0x90000000u<two.size())return two.data()+a-0x90000000u;return nullptr;}
    uint32_t read32(uint32_t a){auto p=get_ptr(a);assert(p&&get_ptr(a+3));return uint32_t(p[0])<<24|uint32_t(p[1])<<16|uint32_t(p[2])<<8|p[3];}
    void write32(uint32_t a,uint32_t w){auto p=get_ptr(a);assert(p&&get_ptr(a+3));for(unsigned i=0;i<4;++i)p[i]=uint8_t(w>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{Mmu mmu;std::array<uint32_t,32> gpr{};std::array<Cr,8> cr{};uint32_t pc=S,lr=O+4,ctr=0,msr=0x8032,dispatch_saved_ctx=0;uint64_t inst_count=100;bool is_running=true,in_callback=false;};
struct Prior{bool ok=true;bool returned(Cpu&,bool held)const{return ok&&held;}};
static void trial(unsigned f){
    Cpu c;c.gpr[1]=0x80008000u;c.gpr[2]=0x80009000u;c.gpr[13]=0x8000a000u;c.gpr[3]=Q;
    const std::array<ReplyNativeWord,7> words{{{S,S,Nop},{S,S+4,Nop},{S,S+8,bl(S+8,R)},{S,S+12,bl(S+12,F)},
        {R,R,Mtmsr},{R,R+4,Blr},{F,F,Nop}}};
    for(auto w:words)c.mmu.write32(w.pc,w.word);
    c.mmu.write32(O,bl(O,S));c.mmu.write32(Q,StmIos::Open);
    SubmitResumeWitness w({S,S+4,O+4,bl(O,S),{R,S+12,bl(S+8,R),Mtmsr},{F,S+16,bl(S+12,F),Nop},words});
    if(f==1)c.gpr[3]+=4;
    bool ok=w.capture(c,true);if(f==1){assert(!ok&&w.failure()==1);return;}assert(ok);
    c.pc=S+4;c.gpr[1]-=64;c.msr=0x32;c.inst_count+=100;c.mmu.write32(Q,StmIos::Reply);c.mmu.write32(Q+8,StmIos::Open);
    if(f==2)c.mmu.write32(Q+4,1);
    ok=w.begin(c,Prior{f!=3},true);if(f==2||f==3){assert(!ok&&w.failure()==2);return;}assert(ok);
    c.inst_count+=2;assert(w.before(c,S+4,Nop,true));c.gpr[3]=f==4?0:1;++c.inst_count;
    ok=w.before(c,S+8,bl(S+8,R),true);if(f==4){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.pc=R;c.lr=S+12;assert(w.entry(c,R,true));c.gpr[4]=f==5?0x32:0x8032;++c.inst_count;
    ok=w.before(c,R,Mtmsr,true);if(f==5){assert(!ok&&w.failure()==4);return;}assert(ok);
    c.msr=0x8032;c.pc=R+4;if(f==6)++c.pc;
    ok=w.poll(c,true);if(f==6){assert(!ok&&w.failure()==6);return;}assert(ok);
    ++c.inst_count;assert(w.before(c,R+4,Blr,true));c.gpr[4]=f==7?Q+32:Q;
    if(f==8)c.mmu.write32(Q+4,1);
    ++c.inst_count;ok=w.before(c,S+12,bl(S+12,F),true);
    if(f==7||f==8){assert(!ok&&w.failure()==(f==7?4u:3u));return;}assert(ok);
    c.pc=F;c.lr=S+16;if(f==9)c.lr+=4;
    ok=w.entry(c,F,true);if(f==9){assert(!ok&&w.failure()==5);return;}assert(ok);
    assert(w.release_at(c,true)&&w.visits()==5);
    if(f==10){++c.inst_count;assert(!w.release_at(c,true));}
}
int main(){for(unsigned f=0;f<=10;++f)trial(f);std::cout<<"V1342_SUBMIT_RESUME synthetic=1 valid=1 refused=10 response_held=1 outer_ee=1 original_execution=0\n";}
