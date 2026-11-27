#include "wii_post_stm_sc_formatter.h"
#include <cassert>
#include <iostream>
#include <limits>
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
// Synthetic joined frames: original computed transfer, partial load and
// two caller stores. The observer predicts effects; the fixture applies
// the independent instruction effects, including deliberately varied bytes.
static void caller_trial(unsigned fault,uint32_t seed){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.mmu.write32(A,T+0x100u);
    for(unsigned i=14;i<32;++i)c.gpr[i]=0x100u+i;
    constexpr uint32_t link=R+20,dst=T+0x100u,site=T+24u,partial=dst+4u;
    const uint32_t stop=dst+(fault>=11?24u:20u);
    const auto parent_sp=SP-704u,child_sp=parent_sp-48u;
    c.mmu.write32(child_sp+8,seed);c.mmu.write32(parent_sp+16,0xfacecafeu);
    const std::array<IpcDispatchWord,5> pp{{{R,R,ins(37,1,1,-704)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,708)},{R,R+12,ins(47,16,1,640)},{R,R+16,bl(R+16,T)}}};
    const std::array<ScFormatterAccess,3> pa{{{R,4,-704,true,true},{R+8,4,4,true,true},{R+12,64,-64,true,true}}};
    std::array<StmFinalSlot,17> ps{};ps[0]={4,32};for(unsigned r=16;r<32;++r)ps[r-15]={int32_t(4*(int(r)-32)),r};
    for(auto x:pp)c.mmu.write32(x.pc,x.word);
    ScFormatterWitness parent({R,L,T,ins(37,1,1,-48),704,pp,pa,ps});
    // Child entry word must be mapped before parent.begin.
    c.mmu.write32(T,ins(37,1,1,-48));
    assert(parent.begin(c,true)&&parent.poll(c,true));++c.inst_count;assert(parent.entry(c,R,true));
    for(auto x:pp){
        ++c.inst_count;assert(parent.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=parent_sp;c.mmu.write32(parent_sp,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else if(x.pc==R+12)for(unsigned r=16;r<32;++r)c.mmu.write32(SP-64+4*(r-16),c.gpr[r]);
        else {c.pc=T;c.lr=link;}
    }
    assert(parent.entry(c,T,true)&&parent.reached(c,true));
    const std::array<IpcDispatchWord,6> cp{{{T,T,ins(37,1,1,-48)},{T,T+4,0x7c0802a6},
        {T,T+8,ins(36,0,1,52)},{T,T+12,ins(44,5,1,8)},{T,T+16,ins(32,6,3,0)},{T,T+20,0x7cc903a6}}};
    const std::array<ScFormatterAccess,4> ca{{{T,4,-48,true,true},{T+8,4,4,true,true},
        {T+12,2,-40,true,true},{T+16,4,A,false,false,dst}}};
    const std::array<StmFinalSlot,1> cs{{{4,32}}};
    const uint32_t branch=0x4e800420u,body=ins(14,7,0,9),load=ins(32,9,1,8),guard=0x60000000u;
    std::vector<IpcDispatchWord> mid(cp.begin(),cp.end());mid.push_back({T,site,branch});mid.push_back({T,dst,body});
    std::vector<IpcDispatchWord> full(mid);full.push_back({T,partial,load});
    full.push_back({T,dst+8,ins(36,7,1,64)});full.push_back({T,dst+12,ins(36,9,1,68)});
    full.push_back({T,dst+16,ins(14,8,7,1)});
    if(fault>=11)full.push_back({T,dst+20,ins(32,10,1,fault==11?68:fault==12?8:fault==13?72:64)});
    std::vector<ScFormatterAccess> more(ca.begin(),ca.end());
    more.push_back({partial,4,-40,true,false});
    more.push_back({dst+8,4,16,true,true});
    more.push_back({dst+12,4,20,true,true});
    if(fault>=11)more.push_back({dst+20,4,fault==11?20:fault==12?-40:fault==13?24:16,true,false});
    if(fault==14)std::swap(more[5],more[7]); // reordered proof must not authorize future writes
    for(auto x:full)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(stop,guard);
    ScFormatterWitness child({T,link,site,branch,48,cp,ca,cs,{}, {dst,body,0x200u}});
    auto held=[&](){return child.has_caller_stores()?parent.child_frame_held_with_stores(c,true,child):
        parent.child_frame_held(c,true,c.gpr[1],child.linkage_word());};
    assert(child.begin(c,parent.frame_held(c,true))&&child.poll(c,held()));++c.inst_count;assert(child.entry(c,T,held()));
    c.gpr[5]=0; // Must match the initial state captured by both witnesses.
    for(auto x:cp){
        ++c.inst_count;assert(child.before(c,x.pc,x.word,held()));
        if(x.pc==T){c.gpr[1]=child_sp;c.mmu.write32(child_sp,parent_sp);}
        else if(x.pc==T+4)c.gpr[0]=link;
        else if(x.pc==T+8)c.mmu.write32(parent_sp+4,link);
        else if(x.pc==T+12){
            // A halfword store leaves the other two bytes physically untouched.
            *c.mmu.get_ptr(child_sp+8)=0;
            *c.mmu.get_ptr(child_sp+9)=0;
        }
        else if(x.pc==T+16)c.gpr[6]=dst;
        else c.ctr=dst;
    }
    ++c.inst_count;assert(child.stop_before_control(c,site,branch,held()));
    c.pc=dst;assert(child.control_transfer_poll(c,held()));++c.inst_count;assert(child.control_destination_entry(c,dst,held()));
    ScFormatterExpectation m{T,link,partial,load,48,mid,ca,cs,{0,4,true,-40}};
    assert(child.resume_control_path(c,m,held()));++c.inst_count;assert(child.before(c,dst,body,held()));c.gpr[7]=9;
    ++c.inst_count;assert(child.stop_before_load(c,partial,load,held()));
    ScFormatterExpectation next{T,link,stop,guard,48,full,more,cs,{0,0,false,0,true}};
    if(fault==1)more[5].address=640;
    if(fault==2)more[6].address=16;
    if(fault==3)more[5].address=4;
    if(fault==4)more[4].address=-36;
    if(fault==5)more[5].address=704;
    if(fault==6)full[8].word^=1u;
    if(fault==17)more[5].address=std::numeric_limits<int64_t>::max()-3;
    if(fault==18)more[7].address=std::numeric_limits<int64_t>::max()-3;
    if(fault==19)more[7].address=std::numeric_limits<int64_t>::min();
    if(fault==20)more[7].address=17;
    const bool resumed=child.resume_stack_path(c,next,parent,fault==7?0xffffu:0xffff0000u,held());
    if((fault>=1&&fault<=7)||fault==13||fault==14||fault>=17){assert(!resumed);return;}assert(resumed);
    c.gpr[9]=seed&0xffffu; // Actual original load would read these live bytes.
    ++c.inst_count;assert(child.before(c,dst+8,full[9].word,held()));
    c.mmu.write32(parent_sp+16,fault==8?10u:9u);
    if(fault==9)c.mmu.write32(parent_sp+24,0x11u);
    ++c.inst_count;const bool ok=child.before(c,dst+12,full[10].word,held());
    if(fault==8||fault==9){assert(!ok);return;}assert(ok);
    c.mmu.write32(parent_sp+20,fault==10?c.gpr[9]^1u:c.gpr[9]);
    ++c.inst_count;const bool ok2=child.before(c,dst+16,full[11].word,held());
    if(fault==10){assert(!ok2);return;}assert(ok2);c.gpr[8]=10;
    if(fault>=11){
        ++c.inst_count;assert(child.before(c,dst+20,full[12].word,held()));
        c.gpr[10]=fault==15?9u:seed&0xffffu;
        if(fault==16)c.gpr[10]^=1u;
    }
    ++c.inst_count;
    const bool stopped=child.stop_before_instruction(c,stop,guard,held());
    if(fault==16){assert(!stopped);return;}
    assert(stopped&&child.reached_instruction_boundary(c,held()));
    assert(child.caller_store_count()==2&&child.visits()==(fault>=11?13u:12u)&&child.loads()==(fault>=11?3u:2u)&&child.stores()==5);
    assert(c.mmu.read32(parent_sp+20)==(seed&0xffffu));
    assert(!parent.child_frame_held(c,true,c.gpr[1],child.linkage_word()));
}
int main(){for(unsigned i=0;i<8;++i)trial(i);
    for(unsigned i=0;i<=20;++i)caller_trial(i,0x1234beefu);
    caller_trial(0,0u);caller_trial(0,0xffffffffu);
    // Each opaque byte position exercises all 256 possible values.
    for(unsigned i=0;i<256;++i)caller_trial(11,0x5a5a0000u|(i<<8)|(255u-i));
    std::cout<<"FORMATTER_NESTED_JOIN_TEST cases=287 original_execution=0\n";}
