#include "wii_post_stm_sc_formatter.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,T=B+0x200u,L=B+0x400u,A=B+0x500u,Sp=B+0xc00u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=L,ctr=1,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=A;for(unsigned i=14;i<32;++i)c.gpr[i]=0x100u+i;
    *c.mmu.get_ptr(A)=0x41u;
    std::array<StmFinalSlot,17> slots{};slots[0]={4,32};
    for(unsigned i=16;i<32;++i)slots[i-15]={int32_t(4*(int(i)-32)),i};
    const std::array<uint32_t,9> ops{{ins(37,1,1,-704),0x7c0802a6,ins(36,0,1,708),
        ins(47,16,1,640),ins(14,5,0,0x7f),ins(38,5,1,fault==7?16:12),
        ins(34,6,3,0),ins(11,0,6,0x41),bl(R+32,T)}};
    std::array<IpcDispatchWord,9> path{};
    for(unsigned i=0;i<path.size();++i){path[i]={R,R+4*i,ops[i]};c.mmu.write32(path[i].pc,path[i].word);}
    c.mmu.write32(T,Nop);
    const std::array<ScFormatterAccess,5> accesses{{{R,4,-704,true,true},{R+8,4,4,true,true},
        {R+12,64,-64,true,true},{R+20,1,-692,true,true},{R+24,1,A,false,false}}};
    ScFormatterWitness w({R,L,T,Nop,fault==2?708u:704u,path,accesses,slots});
    bool ok=w.begin(c,fault!=1);if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    const auto incoming=c.gpr;
    for(unsigned i=0;i<path.size();++i){
        auto x=path[i];++c.inst_count;ok=w.before(c,x.pc,fault==3&&i==0?Nop:x.word,true);
        if(fault==3||(fault==4&&i==1)||(fault==5&&i==3)||(fault==6&&i==4)||(fault==7&&i==5)||
           (fault==8&&i==6)||(fault==9&&i==7)||(fault==10&&i==8)){assert(!ok);return;}assert(ok);
        unsigned op=x.word>>26,rs=(x.word>>21)&31,ra=(x.word>>16)&31;
        uint32_t imm=uint32_t(int32_t((x.word&0xffffu)^0x8000u)-0x8000);
        if(op==37){c.gpr[1]+=imm;c.mmu.write32(c.gpr[1],fault==4?0:Sp);}
        else if(op==31)c.gpr[rs]=L;
        else if(op==36)c.mmu.write32(c.gpr[ra]+imm,fault==5?0:c.gpr[rs]);
        else if(op==47){for(unsigned j=rs;j<32;++j)c.mmu.write32(c.gpr[ra]+imm+4u*(j-rs),fault==6&&j==31?0:c.gpr[j]);}
        else if(op==14)c.gpr[rs]=(ra?c.gpr[ra]:0)+imm;
        else if(op==38)*c.mmu.get_ptr(c.gpr[ra]+imm)=fault==8?0:uint8_t(c.gpr[rs]);
        else if(op==34)c.gpr[rs]=fault==9?0:c.mmu.read8(c.gpr[ra]+imm);
        else if(op==11)c.cr[0].eq=fault!=10;
        else if(op==18){c.lr=x.pc+4;c.pc=T;}
    }
    if(fault==11)c.mmu.write32(Sp-16,0);
    if(fault==12)c.gqr[4]^=1;
    if(fault==13)c.lr=L;
    ok=w.entry(c,fault==14?T+4:T,fault!=15);
    if(fault>=11&&fault<=15){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.visits()==9&&w.stores()==4&&w.loads()==1&&w.linkage_word()==L);
    assert(c.gpr[31]==incoming[31]&&c.mmu.read32(Sp-4)==incoming[31]);
    c.gpr[3]^=0x100u;assert(w.frame_held(c,true)&&!w.reached(c,true));
    assert(!w.frame_held(c,false));c.mmu.write32(Sp-16,0);assert(!w.frame_held(c,true));
}
int main(){for(unsigned i=0;i<=15;++i)trial(i);std::cout<<"POST_STM_SC_FORMATTER_TEST cases=16 original_execution=0\n";}
