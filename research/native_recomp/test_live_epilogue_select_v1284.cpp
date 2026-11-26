#include "wii_live_epilogue_v762.h"
#include "wii_hollywood_irq.h"
#include <cassert>
#include <iostream>
#include <map>
using namespace undercover::wii;
constexpr uint32_t Context=0x80010000u,Resume=0x80004000u,J=0x80008000u,E=0x80009000u,
    D=E+0x100u,R=E+0x200u,S=E+0x300u,L=E+0x400u,G=E+0x500u,
    Sda=0x80012000u,Counter=Sda-8u,Hint=Sda-4u,Other=0x100u,BLR=0x4e800020u,RFI=0x4c000064u,NOP=0x60000000u,Get=G+0x100u;
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Mmu{
    std::map<uint32_t,uint32_t> words;uint8_t b=0;
    uint8_t* get_ptr(uint32_t a){return words.count(a&~3u)?&b:nullptr;}
    uint32_t read32(uint32_t a){return words.at(a);}
    uint16_t read16(uint32_t a){return uint16_t(read32(a&~3u)>>(a&2u?0:16));}
};
struct Cpu{
    Mmu mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Resume,lr=Resume+4u,msr=0x8032u,ctr=17u,xer=0x80000000u,
        srr0=0,srr1=0,dispatch_saved_ctx=0;
    uint64_t inst_count=100u;bool is_running=true,in_callback=false;
};
static void trial(uint32_t source,unsigned fault,bool cleared=false){
    Cpu c;auto& m=c.mmu.words;ExternalReturnWitness frame;
    for(unsigned i=0;i<32;++i)c.gpr[i]=i*17u+3u;
    c.gpr[13]=Sda;c.gqr[3]=0x00040004u;c.cr[0].eq=true;
    const auto gp=c.gpr;const auto gq=c.gqr;const auto cr=c.cr;
    const auto lr=c.lr,msr=c.msr,ctr=c.ctr,xer=c.xer;
    const uint32_t cause=cleared?Other:Other|source,mask=source;
    assert(frame.capture(c,Other|source,mask,source));
    for(unsigned i=0;i<32;++i)m[Context+4u*i]=gp[i];
    m[Context+128u]=0x20000000u;m[Context+132u]=lr;m[Context+136u]=ctr;m[Context+140u]=xer;
    m[Context+408u]=Resume;m[Context+412u]=msr;m[Context+0x1a0u]=2u;
    for(unsigned i=0;i<8;++i)m[Context+0x1a4u+4u*i]=gq[i];
    m[Counter]=1;m[Hint]=0;
    m[J]=bl(J,E);m[J+4u]=bl(J+4u,S);m[J+8u]=NOP;m[J+12u]=bl(J+12u,L);
    m[E]=bl(E,D);m[E+4u]=bl(E+4u,R);m[E+8u]=BLR;m[D]=BLR;m[R]=BLR;m[S]=BLR;m[L]=RFI;
    c.msr=0x32u;c.pc=J;c.gpr[30]=Context;c.inst_count+=100u;
    m[S]=0x48000000u|((G-S)&0x03fffffcu);m[G]=bl(G,Get);m[G+4u]=NOP;m[G+8u]=BLR;m[Get]=BLR;
    LiveEpilogueWitness w({J,E,S,D,R,L,G,Context,-8,-4,30,255,Get,G+4u,S});
    if(fault==1)m[Context+124u]^=1;
    if(fault==2)m[Counter]=0;
    const bool begun=cleared?w.begin_cleared_select(c,frame,fault==3?(Other|source):cause,mask):
        w.begin_pending(c,frame,fault==3?Other:cause,mask);
    if(fault>=1&&fault<=3){assert(!begun&&w.failure()==1u);return;}
    assert(begun);
    auto step=[&](uint32_t pc){c.pc=pc;++c.inst_count;return w.before(c,pc,m.at(pc),cause,mask);};
    auto entry=[&](uint32_t pc,uint32_t ret){c.pc=pc;c.lr=ret;return w.entry(c,pc,cause,mask);};
    // begin_pending runs inside the first instruction hook.
    --c.inst_count;
    assert(step(J)&&entry(E,J+4u)&&step(E)&&entry(D,E+4u)&&step(D));
    c.lr=J+4u; // model caller restoring LR only after nested calls
    if(fault==4){assert(step(E+4u));
        c.pc=R;c.lr=E+12u;assert(!w.entry(c,R,cause,mask)&&w.failure()==2u);return;}
    assert(step(E+4u)&&entry(R,E+8u)&&step(R));c.lr=J+4u;
    assert(step(E+8u));c.gpr[3]=1u;if(fault!=5)m[Counter]=0;
    bool ok=step(J+4u);if(fault==5){assert(!ok&&w.failure()==4u);return;}assert(ok);
    assert(entry(S,J+8u));c.gpr[3]=fault==6?1u:0u;m[Hint]=1u;
    ok=step(S);if(fault==6){assert(!ok&&w.failure()==7u);return;}assert(ok&&w.select_state()==1u);
    c.pc=G;
    if(fault==11)++c.inst_count;
    ok=w.poll(c,cause,mask);if(fault==11){assert(!ok&&w.failure()==8u);return;}assert(ok);
    ++c.inst_count;
    if(fault==12)c.lr+=4u;
    ok=w.entry(c,G,cause,mask);if(fault==12){assert(!ok&&w.failure()==2u);return;}assert(ok);
    assert(step(G)&&entry(Get,G+4u)&&step(Get));c.gpr[3]=fault==13?Context+4u:Context;
    ok=step(G+4u);if(fault==13){assert(!ok&&w.failure()==7u);return;}assert(ok);
    c.lr=J+8u;assert(step(G+8u)&&w.select_state()==4u);c.pc=J+8u;
    assert(w.poll(c,cause,mask));
    if(fault!=14)++c.inst_count;
    ok=step(J+8u);if(fault==14){assert(!ok&&w.failure()==3u);return;}assert(ok&&w.select_state()==6u);
    c.gpr[3]=Context;assert(step(J+12u)&&entry(L,J+16u));
    c.gpr=gp;c.gqr=gq;c.cr=cr;c.lr=lr;c.ctr=ctr;c.xer=xer;c.srr0=Resume;c.srr1=msr;
    m[Context+0x1a0u]=0u;
    if(fault==7)c.gqr[3]^=1u;
    if(fault==8)c.gpr[31]^=1u;
    ok=step(L);if(fault==7||fault==8){assert(!ok&&w.failure()==5u);return;}
    assert(ok&&w.stage()==2u);
    c.pc=Resume;c.msr=msr;
    if(fault==9)++c.inst_count;
    if(fault==10)c.gqr[3]^=1u;
    ok=cleared?w.poll(c,cause,mask):w.pending_rfi_return(c,cause,mask);
    if(fault==9||fault==10){assert(!ok&&w.failure()==8u);return;}
    assert(ok&&w.stage()==3u);
    if(cleared){
        if(fault==15)++c.inst_count;
        ok=w.poll(c,cause,mask);
        if(fault==15){assert(!ok&&w.failure()==8u);return;}
        assert(ok&&w.stage()==4u&&frame.stage()==4u);
    }else assert(frame.pending_restored(c,cause,mask));
}
int main(){
    for(uint32_t source:{8u,HollywoodIrq::PI_HOLLYWOOD}){
        for(unsigned fault=0;fault<=14;++fault)trial(source,fault);
    }
    std::cout<<"V1284_SELECT_EPILOGUE synthetic=1 valid=2 refused=28 tail=1 getter=1 outer_ticks=2 original_rfi=0\n";
    for(unsigned fault=0;fault<=15;++fault)trial(HollywoodIrq::PI_HOLLYWOOD,fault,true);
    std::cout<<"V1303_CLEARED_SELECT synthetic=1 valid=1 refused=15 same_idle_rfi=1 original_execution=0\n";
}
