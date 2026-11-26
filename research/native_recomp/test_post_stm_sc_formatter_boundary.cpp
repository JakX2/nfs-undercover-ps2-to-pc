#include "wii_post_stm_sc_formatter.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,L=B+0x400u,A=B+0x500u,SP=B+0xc00u;
constexpr uint32_t ins(unsigned op,unsigned r,unsigned a,int n){return (op<<26)|(r<<21)|(a<<16)|(uint32_t(n)&0xffffu);}
struct Mem{
    std::array<uint8_t,4096> ram{};unsigned data_reads=0;
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){if(a>=A&&a<A+4)++data_reads;auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=L,ctr=0,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.gpr[31]=0x1234;
    c.mmu.write32(A,0xdeadbeefu);
    constexpr uint32_t target=R+16,load=ins(32,4,3,0);
    const std::array<IpcDispatchWord,4> path{{{R,R,ins(37,1,1,-48)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,52)},{R,R+12,ins(36,31,1,44)}}};
    const std::array<ScFormatterAccess,3> access{{{R,4,-48,true,true},{R+8,4,4,true,true},{R+12,4,-4,true,true}}};
    const std::array<StmFinalSlot,2> slots{{{4,32},{-4,31}}};
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(target,load);
    ScFormatterWitness w({R,L,target,load,48,path,access,slots,{fault==1?A+1:fault==2?A+4:A,fault==3?2u:4u}});
    bool ok=w.begin(c,true);
    if(fault==1||fault==3){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    for(auto x:path){
        ++c.inst_count;assert(w.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=SP-48;c.mmu.write32(SP-48,SP);}
        if(x.pc==R+4)c.gpr[0]=L;
        if(x.pc==R+8)c.mmu.write32(SP+4,L);
        if(x.pc==R+12)c.mmu.write32(SP-4,c.gpr[31]);
    }
    if(fault==4)c.mmu.write32(SP-4,0);
    if(fault==5)c.gpr[4]=0xdeadbeefu;
    if(fault==6)c.mmu.write32(target,ins(34,4,3,0));
    if(fault!=7)++c.inst_count;
    ok=w.stop_before_load(c,target,load,fault!=8);
    if(fault){assert(!ok);return;}
    assert(ok&&w.reached_load_boundary(c,true)&&!w.reached(c,true));
    assert(w.visits()==4&&w.stores()==3&&w.loads()==0&&c.gpr[4]==0&&c.mmu.data_reads==0);
    ++c.inst_count;assert(!w.reached_load_boundary(c,true));
}
int main(){for(unsigned i=0;i<=8;++i)trial(i);std::cout<<"FORMATTER_BOUNDARY_TEST cases=9 original_execution=0\n";}
