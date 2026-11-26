#include "wii_post_stm_sc_report_helper.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,T=B+0x200u,L=B+0x400u,Sp=B+0x900u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t mr(unsigned ra,unsigned rs){return (31u<<26)|(rs<<21)|(ra<<16)|(rs<<11)|(444u<<1);}
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
    Cpu c;c.gpr[1]=Sp;for(unsigned i=3;i<32;++i)c.gpr[i]=0x100u+i;
    const std::array<StmFinalSlot,4> slots{{{4,32},{-4,31},{-8,30},{-12,29}}};
    const std::array<uint32_t,13> ops{{ins(37,1,1,-32),0x7c0802a6,ins(36,0,1,36),
        ins(36,31,1,28),ins(36,30,1,24),ins(36,29,1,20),mr(31,3),mr(30,4),
        ins(14,29,0,1),ins(14,3,31,0),ins(14,4,30,0),ins(14,5,0,0),bl(R+48,T)}};
    std::array<IpcDispatchWord,13> words{};
    for(unsigned i=0;i<words.size();++i){words[i]={R,R+4*i,ops[i]};c.mmu.write32(words[i].pc,ops[i]);}
    c.mmu.write32(T,Nop);ScReportHelperWitness w({R,L,T,Nop,32,words,slots});
    bool ok=w.begin(c,fault!=1);if(fault==1){assert(!ok);return;}assert(ok&&w.poll(c,true));
    ++c.inst_count;assert(w.entry(c,R,true));
    for(unsigned i=0;i<words.size();++i){
        auto x=words[i];++c.inst_count;ok=w.before(c,x.pc,fault==2&&i==0?Nop:x.word,true);
        if(fault==2||(fault==3&&i==1)||(fault==4&&i==3)||(fault==5&&i==4)||(fault==6&&i==7)||
           (fault==7&&i==9)||(fault==8&&i==12)){assert(!ok);return;}assert(ok);
        unsigned op=x.word>>26,rs=(x.word>>21)&31,ra=(x.word>>16)&31;
        uint32_t imm=uint32_t(int32_t((x.word&0xffffu)^0x8000u)-0x8000);
        if(op==37){c.gpr[1]+=imm;c.mmu.write32(c.gpr[1],fault==3?0:Sp);}
        else if(op==31){if(((x.word>>1)&1023)==339)c.gpr[rs]=L;else c.gpr[ra]=c.gpr[rs];}
        else if(op==36)c.mmu.write32(c.gpr[ra]+imm,(fault==4&&i==2)||(fault==5&&i==3)?0:c.gpr[rs]);
        else if(op==14)c.gpr[rs]=(ra?c.gpr[ra]:0)+imm;
        else if(op==18){c.lr=x.pc+4;c.pc=T;}
        if(fault==6&&i==6)c.gpr[31]^=1;
        if(fault==7&&i==8)c.gqr[4]^=1;
        if(fault==8&&i==11)c.mmu.write32(Sp-16,1);
    }
    if(fault==9)c.lr=L;
    ok=w.entry(c,fault==10?T+4:T,fault!=11);
    if(fault>=9&&fault<=11){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.visits()==13&&w.stores()==5&&w.linkage_word()==L);
    const auto parent=c.gpr[1];const auto child_link=R+52;
    c.mmu.write32(parent+4,child_link);c.gpr[1]=parent-704;
    assert(w.child_frame_held(c,true,c.gpr[1],child_link,704));
    c.gpr[1]-=48;
    assert(!w.child_frame_held(c,true,c.gpr[1],child_link,752));
    assert(w.child_frame_held(c,true,c.gpr[1],child_link,752,48));
    assert(!w.child_frame_held(c,true,c.gpr[1],child_link,752,56));
    assert(!w.child_frame_held(c,true,c.gpr[1],child_link+4,752,48));
    c.mmu.write32(Sp-4,0);assert(!w.child_frame_held(c,true,c.gpr[1],child_link,752,48));
}
int main(){for(unsigned i=0;i<=11;++i)trial(i);std::cout<<"POST_STM_SC_REPORT_HELPER_TEST cases=12 original_execution=0\n";}
