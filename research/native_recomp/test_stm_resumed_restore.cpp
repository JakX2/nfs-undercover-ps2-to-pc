#include "wii_stm_resumed_restore.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t Base=0x80000000u,Root=Base+0x100u,Resume=Root+4u,Caller=Base+0x200u;
constexpr uint32_t Rotate=(21u<<26)|(4u<<21)|(3u<<16)|(17u<<11)|(31u<<6)|(31u<<1);
constexpr uint32_t Isync=0x4c00012cu,Ret=0x4e800020u,Nop=0x60000000u;
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=Base&&a-Base<ram.size()?ram.data()+a-Base:nullptr;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);v=(v<<8)|*p;}return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=Caller,ctr=1,xer=2,msr=0x8032,srr0=Resume,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(bool old_ee,unsigned fault){
    Cpu c;c.gpr[4]=old_ee?0x8000u:0u;c.gpr[1]=Base+0x800;c.gqr[4]=0x1234;
    const uint32_t first=fault==7?0x90610000u:fault==8?(Rotate|1u):fault==9?
        ((Rotate&~(31u<<16))|(14u<<16)):Rotate;
    std::array<IpcDispatchWord,3> words{{{Root,Resume,first},{Root,Resume+4,Isync},{Root,Resume+8,Ret}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Caller,Nop);
    StmResumedRestoreWitness w({Root,Caller,Nop,Root,Resume,first,words});
    if(fault==1)c.lr+=4;
    bool ok=w.begin(c,fault!=2);
    if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    if(fault==3){++c.inst_count;assert(!w.poll(c,true));return;}
    assert(w.poll(c,true));c.inst_count+=fault==4?1u:2u;
    ok=w.before(c,Resume,fault==5?Nop:first,true,fault!=6);
    if(fault>=4&&fault<=9){assert(!ok);return;}assert(ok);
    c.gpr[3]=fault==10?unsigned(!old_ee):unsigned(old_ee);
    if(fault==11)c.gqr[4]^=1;
    ++c.inst_count;ok=w.before(c,Resume+4,Isync,true,false);
    if(fault==10||fault==11){assert(!ok);return;}assert(ok);
    if(fault==12)c.gpr[31]^=1;
    ++c.inst_count;ok=w.before(c,Resume+8,Ret,true,false);
    if(fault==12){assert(!ok);return;}assert(ok);
    c.pc=fault==13?Caller+4:Caller;
    ok=w.poll(c,fault!=14);
    if(fault==13||fault==14){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==3);
    if(fault==15){++c.inst_count;assert(!w.reached(c,true));}
}
int main(){for(bool ee:{false,true})for(unsigned f=0;f<=15;++f)trial(ee,f);
    std::cout<<"STM_RESUMED_RESTORE_TEST cases=32 original_execution=0\n";}
