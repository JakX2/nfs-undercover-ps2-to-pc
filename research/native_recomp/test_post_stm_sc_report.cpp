#include "wii_post_stm_sc_report.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,T=B+0x200u,Sp=B+0x900u,Nop=0x60000000u;
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
    uint32_t pc=R,lr=B+0x400u,ctr=1,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Sp;for(unsigned i=3;i<11;++i)c.gpr[i]=0x100u+i;
    std::vector<IpcDispatchWord> path;
    auto emit=[&](uint32_t w){path.push_back({R,R+4u*uint32_t(path.size()),w});};
    emit(ins(37,1,1,-128));emit(0x7c0802a6);emit(ins(36,0,1,132));
    for(unsigned i=3;i<11;++i)emit(ins(36,i,1,32+4*int(i-3)));
    emit(ins(15,0,0,0x100));emit(ins(36,0,1,8));emit(ins(14,0,1,136));emit(ins(36,0,1,12));
    emit(ins(14,0,1,32));emit(ins(36,0,1,16));emit(ins(14,4,1,8));emit(bl(R+4u*uint32_t(path.size()),T));
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(T,Nop);if(fault==2)c.cr[1].eq=true;
    ScReportWitness w({R,T,Nop,128,path,13});
    bool ok=w.begin(c,fault!=1);if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    const auto incoming=c.gpr;const auto lr=c.lr;
    for(unsigned i=0;i<path.size();++i){
        auto x=path[i];++c.inst_count;ok=w.before(c,x.pc,fault==3&&i==0?Nop:x.word,true);
        if(fault==3||(fault==4&&i==1)||(fault==5&&i==3)||(fault==6&&i==8)||(fault==7&&i==13)||
           (fault==8&&i==18)||(fault==9&&i==5)){assert(!ok);return;}assert(ok);
        unsigned op=x.word>>26,rs=(x.word>>21)&31,ra=(x.word>>16)&31;
        uint32_t imm=uint32_t(int32_t((x.word&0xffffu)^0x8000u)-0x8000);
        if(op==37){c.gpr[1]+=imm;c.mmu.write32(c.gpr[1],fault==4?0:Sp);}
        else if(op==31)c.gpr[rs]=lr;
        else if(op==36)c.mmu.write32(c.gpr[ra]+imm,(fault==5&&i==2)||(fault==6&&i==7)||(fault==7&&i==12)?0:c.gpr[rs]);
        else if(op==14||op==15)c.gpr[rs]=(ra?c.gpr[ra]:0)+(op==15?imm<<16:imm);
        else if(op==18){c.lr=x.pc+4;c.pc=T;}
        if(fault==8&&i==17)c.gpr[4]+=4;
        if(fault==9&&i==4)c.gqr[4]^=1;
    }
    if(fault==10)c.lr=lr;
    if(fault==11)c.mmu.write32(Sp-4,1);
    ok=w.entry(c,fault==12?T+4:T,fault!=13);
    if(fault>=10&&fault<=13){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.stores()==13&&w.visits()==path.size()&&w.linkage_word()==lr&&c.gpr[3]==incoming[3]);
}
static void branch_check(bool wrong){
    Cpu c;c.gpr[1]=Sp;
    const uint32_t branch=wrong?0x41860008u:0x40860008u;
    const std::array<IpcDispatchWord,3> path{{{R,R,ins(37,1,1,-128)},
        {R,R+4,branch},{R,R+12,Nop}}};
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(T,Nop);
    ScReportWitness w({R,T,Nop,128,path,14});
    assert(w.begin(c,true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    ++c.inst_count;assert(w.before(c,R,path[0].word,true));
    c.gpr[1]-=128;c.mmu.write32(c.gpr[1],Sp);
    ++c.inst_count;assert(w.before(c,R+4,branch,true)==!wrong);
}
static void missing_entry(){
    Cpu c;c.gpr[1]=Sp;
    const std::array<IpcDispatchWord,1> path{{{R,R,ins(37,1,1,-128)}}};
    c.mmu.write32(R,path[0].word);c.mmu.write32(T,Nop);
    ScReportWitness w({R,T,Nop,128,path,1});
    assert(w.begin(c,true)&&w.poll(c,true));c.inst_count+=2;
    assert(!w.before(c,R,path[0].word,true));
}
int main(){for(unsigned i=0;i<=13;++i)trial(i);branch_check(false);branch_check(true);missing_entry();
    std::cout<<"POST_STM_SC_REPORT_TEST cases=17 original_execution=0\n";}
