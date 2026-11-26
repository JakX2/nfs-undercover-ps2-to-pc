#include "wii_post_stm_sc_leaf_shadow.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,L=B+0x200u,A=B+0x500u,Sp=B+0x900u,Nop=0x60000000u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
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
static void trial(unsigned fault,bool zero){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=A;c.mmu.write32(A,zero?0u:0x1234u);c.mmu.write32(A+4,0xaabbccddu);
    const std::array<IpcDispatchWord,7> words{{{R,R,ins(32,5,3,0)},{R,R+4,ins(11,0,5,0)},
        {R,R+8,0x41820010u},{R,R+12,ins(14,5,5,1)},{R,R+16,ins(36,5,3,fault==9?8:4)},
        {R,R+20,0x4e800020u},{R,R+24,0x4e800020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(L,Nop);
    const std::array<ScLeafAccess,2> accesses{{{R,0,4,false},{R+16,4,4,true}}};
    ScLeafShadow w({R,L,Nop,words,accesses});
    bool ok=w.begin(c,{A,fault==2?4u:8u},fault!=1);
    if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,fault==3&&i==0?Nop:words[i].word,true);};
    ok=step(0);if(fault==3){assert(!ok);return;}assert(ok);
    c.gpr[5]=fault==4?0xffffffffu:c.mmu.read32(A);
    ok=step(1);if(fault==4){assert(!ok);return;}assert(ok);
    c.cr[0].eq=zero;c.cr[0].gt=!zero;
    if(fault==5)c.cr[0].eq=!zero;
    ok=step(2);if(fault==5){assert(!ok);return;}assert(ok);
    if(zero){assert(step(6));c.pc=L;assert(w.poll(c,true)&&w.reached(c,true)&&w.stores()==0);return;}
    if(fault==6){assert(!step(6));return;}
    assert(step(3));++c.gpr[5];if(fault==7)c.gpr[5]^=1;if(fault==8)c.mmu.write32(A,0);
    ok=step(4);if(fault>=7&&fault<=9){assert(!ok);return;}assert(ok);
    c.mmu.write32(A+4,fault==10?0:c.gpr[5]);if(fault==11)c.gqr[4]^=1;
    ok=step(5);if(fault==10||fault==11){assert(!ok);return;}assert(ok);
    c.pc=fault==12?L+4:L;ok=w.poll(c,fault!=13);if(fault==12||fault==13){assert(!ok);return;}
    assert(ok&&w.reached(c,true)&&w.visits()==6&&w.loads()==1&&w.stores()==1);
}
static void rotate(unsigned fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=A;c.gpr[4]=0x12345678u;c.gpr[5]=0xaabbccddu;
    // rlwinm extracts a byte, rlwimi merges it into a distinct byte.
    const auto rot=[](unsigned op,unsigned rs,unsigned ra,unsigned sh,unsigned mb,unsigned me,bool rc){
        return (op<<26)|(rs<<21)|(ra<<16)|(sh<<11)|(mb<<6)|(me<<1)|unsigned(rc);
    };
    const std::array<IpcDispatchWord,4> words{{{R,R,rot(21,4,6,8,24,31,true)},
        {R,R+4,rot(20,6,5,16,8,15,false)},{R,R+8,ins(36,5,3,0)},{R,R+12,0x4e800020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(L,Nop);
    const std::array<ScLeafAccess,1> accesses{{{R+8,0,4,true}}};
    ScLeafShadow w({R,L,Nop,words,accesses});
    assert(w.begin(c,{A,8},true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,words[i].word,true);};
    assert(step(0));c.gpr[6]=fault==1?0x78u:0x12u;c.cr[0].gt=fault!=2;
    bool ok=step(1);if(fault==1||fault==2){assert(!ok);return;}assert(ok);
    c.gpr[5]=fault==3?0xaa00ccddu:0xaa12ccddu;
    ok=step(2);if(fault==3){assert(!ok);return;}assert(ok);
    c.mmu.write32(A,c.gpr[5]);assert(step(3));c.pc=L;assert(w.poll(c,true)&&w.reached(c,true));
}
static void signed_compare(bool fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=A;c.gpr[4]=0xffffffffu;
    const std::array<IpcDispatchWord,2> words{{{R,R,ins(11,0,4,0)},{R,R+4,0x4e800020u}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(L,Nop);
    ScLeafShadow w({R,L,Nop,words,{}});
    assert(w.begin(c,{A,4},true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    ++c.inst_count;assert(w.before(c,R,words[0].word,true));c.cr[0].lt=!fault;c.cr[0].gt=fault;
    ++c.inst_count;bool ok=w.before(c,R+4,words[1].word,true);
    if(fault){assert(!ok);return;}assert(ok);c.pc=L;assert(w.poll(c,true)&&w.reached(c,true));
}
static void resumed_call(unsigned fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[3]=A;c.gpr[4]=7;c.pc=R+16;c.lr=R+16;
    constexpr uint32_t S=R+16,T=L+16;
    const auto call=0x48000001u|((T-(S+8))&0x03fffffcu);
    const std::array<IpcDispatchWord,3> words{{{R,S,ins(11,0,4,0)},{R,S+4,ins(14,3,3,4)},{R,S+8,call}}};
    for(auto x:words)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(T,Nop);
    ScLeafShadow w({R,S,words[0].word,words,{},S,T,Nop});
    assert(w.begin(c,{A,8},true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,S,true));
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,words[i].pc,words[i].word,true);};
    assert(step(0));c.cr[0].gt=true;assert(step(1));c.gpr[3]+=4;
    assert(step(2));c.pc=T;c.lr=fault==1?S:S+12;
    bool ok=w.entry(c,fault==2?T+4:T,true);
    if(fault){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==3&&w.stores()==0);
}
int main(){for(unsigned i=0;i<=2;++i)resumed_call(i);for(unsigned i=0;i<=13;++i)trial(i,false);trial(0,true);for(unsigned i=0;i<=3;++i)rotate(i);
    signed_compare(false);signed_compare(true);
    std::cout<<"POST_STM_SC_LEAF_SHADOW_TEST cases=24 original_execution=0\n";}
