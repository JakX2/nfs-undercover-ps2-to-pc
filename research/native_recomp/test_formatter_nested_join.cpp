#include "wii_post_stm_sc_formatter.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,T=B+0x200u,L=B+0x400u,A=B+0x500u,SP=B+0xe00u;
constexpr uint32_t ins(unsigned op,unsigned r,unsigned a,int n){return (op<<26)|(r<<21)|(a<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem {
    std::array<uint8_t,4096> ram{};
    unsigned unresolved_reads=0;
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){if(a>=A+4&&a<A+8)++unresolved_reads;auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=L,ctr=1,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
// Independent synthetic instruction effects; no owner code.
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.mmu.write32(A,0x12345678);
    for(unsigned i=14;i<32;++i)c.gpr[i]=0x100u+i;
    constexpr uint32_t link=R+20,stop=T+24,load=ins(32,7,3,4);
    const std::array<IpcDispatchWord,5> parent_path{{{R,R,ins(37,1,1,-704)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,708)},{R,R+12,ins(47,16,1,640)},{R,R+16,bl(R+16,T)}}};
    const std::array<ScFormatterAccess,3> pa{{{R,4,-704,true,true},{R+8,4,4,true,true},{R+12,64,-64,true,true}}};
    std::array<StmFinalSlot,17> ps{};ps[0]={4,32};for(unsigned r=16;r<32;++r)ps[r-15]={int32_t(4*(int(r)-32)),r};
    const std::array<IpcDispatchWord,6> child_path{{{T,T,ins(37,1,1,-48)},{T,T+4,0x7c0802a6},
        {T,T+8,ins(36,0,1,52)},{T,T+12,ins(36,31,1,44)},{T,T+16,ins(14,31,31,1)},{T,T+20,ins(32,6,3,0)}}};
    const std::array<ScFormatterAccess,4> ca{{{T,4,-48,true,true},{T+8,4,4,true,true},{T+12,4,-4,true,true},
        {T+20,4,A,false,false,0x12345678u}}};
    const std::array<StmFinalSlot,2> cs{{{4,32},{-4,31}}};
    for(auto x:parent_path)c.mmu.write32(x.pc,x.word);
    for(auto x:child_path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(stop,load);
    ScFormatterWitness parent({R,L,T,child_path[0].word,704,parent_path,pa,ps});
    assert(parent.begin(c,true)&&parent.poll(c,true));++c.inst_count;assert(parent.entry(c,R,true));
    for(auto x:parent_path){
        ++c.inst_count;assert(parent.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=SP-704;c.mmu.write32(SP-704,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else if(x.pc==R+12)for(unsigned r=16;r<32;++r)c.mmu.write32(SP-64+4*(r-16),c.gpr[r]);
        else if(x.pc==R+16){c.pc=T;c.lr=link;}
    }
    assert(parent.entry(c,T,true)&&parent.reached(c,true));
    const auto parent_sp=c.gpr[1];
    ScFormatterWitness child({T,link,stop,load,48,child_path,ca,cs,{A+4,4}});
    assert(child.begin(c,parent.frame_held(c,true)));
    auto held=[&](bool device=true){return parent.child_frame_held(c,device,c.gpr[1],child.linkage_word());};
    assert(child.poll(c,held()));++c.inst_count;assert(child.entry(c,T,held()));
    for(auto x:child_path){
        ++c.inst_count;
        const bool ok=child.before(c,x.pc,x.word,held());
        if((fault==1&&x.pc==T+12)||(fault==2&&x.pc==T+12)||(fault==3&&x.pc==T+16)||
           (fault==4&&x.pc==T+20)){assert(!ok);return;}
        assert(ok);
        if(x.pc==T){c.gpr[1]-=48;c.mmu.write32(c.gpr[1],parent_sp);}
        else if(x.pc==T+4)c.gpr[0]=link;
        else if(x.pc==T+8){
            c.mmu.write32(parent_sp+4,fault==1?link+4:link);
            if(fault==2)c.mmu.write32(SP-4,0);
        }else if(x.pc==T+12)c.mmu.write32(parent_sp-4,fault==3?0:c.gpr[31]);
        else if(x.pc==T+16){++c.gpr[31];if(fault==4)c.mmu.write32(A,0);}
        else if(x.pc==T+20)c.gpr[6]=0x12345678;
    }
    if(fault==5)c.gpr[3]+=4;
    if(fault==7)c.gpr[1]-=8;
    ++c.inst_count;const bool ok=child.stop_before_load(c,stop,load,held(fault!=6));
    if(fault>=5){assert(!ok);return;}
    assert(ok&&child.reached_load_boundary(c,held())&&!parent.frame_held(c,true));
    assert(child.visits()==6&&child.loads()==1&&child.authenticated_loads()==1&&child.stores()==3&&c.mmu.unresolved_reads==0);
}
int main(){for(unsigned i=0;i<8;++i)trial(i);std::cout<<"FORMATTER_NESTED_JOIN_TEST cases=8 original_execution=0\n";}
