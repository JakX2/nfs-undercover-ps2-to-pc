#include "wii_post_stm_sc_entry.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t Base=0x80000000u,Caller=Base+0x100u,Root=Base+0x200u,Disable=Base+0x300u,
    Sp=Base+0x800u,Nop=0x60000000u,Mflr=0x7c0802a6u;
constexpr uint32_t ins(unsigned op,unsigned rs,unsigned ra,int n){return (op<<26)|(rs<<21)|(ra<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t bl(uint32_t pc,uint32_t dst){return 0x48000001u|((dst-pc)&0x03fffffcu);}
struct Mem{
    std::array<uint8_t,4096> ram{};
    uint8_t* get_ptr(uint32_t a){return a>=Base&&a-Base<ram.size()?ram.data()+a-Base:nullptr;}
    uint8_t read8(uint32_t a){auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i){auto p=get_ptr(a+i);assert(p);*p=uint8_t(v>>(24-8*i));}}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=Caller,lr=Caller,ctr=1,xer=2,msr=0x8032,srr0=Root,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=Sp;c.gpr[31]=0xaabbccddu;
    const std::array<StmFinalSlot,2> slots{{{4,32},{-4,31}}};
    const std::array<IpcDispatchWord,6> code{{{Caller,Caller,bl(Caller,fault==5?Root+4:Root)},
      {Root,Root,ins(37,1,1,-32)},{Root,Root+4,Mflr},{Root,Root+8,ins(36,0,1,36)},
      {Root,Root+12,ins(36,31,1,fault==10?24:28)},{Root,Root+16,bl(Root+16,Disable)}}};
    for(auto x:code)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(Disable,Nop);
    PostStmScEntryWitness w({Caller,Root,Disable,Nop,32,slots,code});
    bool ok=w.begin(c,fault!=1);if(fault==1){assert(!ok);return;}assert(ok);
    if(fault==2)++c.inst_count;
    ok=w.poll(c,true);if(fault==2){assert(!ok);return;}assert(ok);
    ++c.inst_count;ok=w.entry(c,fault==3?Caller+4:Caller,true);
    if(fault==3){assert(!ok);return;}assert(ok);
    auto step=[&](unsigned i){++c.inst_count;return w.before(c,code[i].pc,fault==4&&i==0?Nop:code[i].word,true);};
    ok=step(0);if(fault==4||fault==5){assert(!ok);return;}assert(ok);
    c.lr=fault==6?Caller:Caller+4;c.pc=Root;
    ok=w.entry(c,Root,true);if(fault==6){assert(!ok);return;}assert(ok);
    assert(step(1));c.gpr[1]=Sp-32;c.mmu.write32(Sp-32,fault==7?Sp+4:Sp);
    ok=step(2);if(fault==7){assert(!ok);return;}assert(ok);
    c.gpr[0]=fault==8?Caller:Caller+4;
    ok=step(3);if(fault==8){assert(!ok);return;}assert(ok);
    c.mmu.write32(Sp+4,Caller+4);if(fault==9)c.mmu.write32(Sp-16,1);
    ok=step(4);if(fault==9||fault==10){assert(!ok);return;}assert(ok);
    c.mmu.write32(Sp-4,c.gpr[31]);if(fault==11)c.gqr[3]^=1;
    ok=step(5);if(fault==11){assert(!ok);return;}assert(ok);
    c.lr=Root+20;c.pc=fault==12?Disable+4:Disable;
    ok=w.entry(c,c.pc,fault!=13);if(fault==12||fault==13){assert(!ok);return;}assert(ok&&w.reached(c,true)&&w.visits()==6&&w.stores()==3);
    assert(w.frame_held(c,true));
    if(fault==14){++c.inst_count;assert(!w.reached(c,true));}
    if(fault==15){c.msr&=~0x8000u;c.gpr[3]=1;assert(w.frame_held(c,true));}
    if(fault==16){c.mmu.write32(Sp-16,1);assert(!w.frame_held(c,true));}
    if(fault==17){c.gpr[1]+=4;assert(!w.frame_held(c,true));}
    if(fault==18){c.inst_count+=129;assert(!w.frame_held(c,true));}
    if(fault>=19){
        constexpr uint32_t child=Sp-32-128,link=Root+0x40;
        c.gpr[1]=child;c.mmu.write32(Sp-28,link);
        assert(w.nested_frame_held(c,true,child,link));
        assert(!w.frame_held(c,true));
        if(fault==20){c.mmu.write32(Sp-28,link+4);assert(!w.nested_frame_held(c,true,child,link));}
        if(fault==21){c.mmu.write32(Sp-4,0);assert(!w.nested_frame_held(c,true,child,link));}
        if(fault==22){c.mmu.write32(Sp+4,0);assert(!w.nested_frame_held(c,true,child,link));}
        if(fault==23){c.gpr[1]=Sp-32-520;assert(!w.nested_frame_held(c,true,c.gpr[1],link));}
        if(fault==24){assert(!w.nested_frame_held(c,false,child,link));}
        if(fault==25){c.mmu.write32(Sp-32,0);assert(!w.nested_frame_held(c,true,child,link));}
        if(fault==26){c.inst_count+=129;assert(!w.nested_frame_held(c,true,child,link));}
        if(fault>=27){
            c.inst_count+=fault==28?257u:256u;
            assert(!w.nested_frame_held_after_checkpoint(c,true,child,link,512u,1u));
            const bool captured=w.capture_nested_checkpoint(c,fault!=29,child,link,512u);
            if(fault==28||fault==29){assert(!captured);return;}
            assert(captured&&w.nested_checkpoint_valid()&&w.nested_checkpoint_age()==256u);
            assert(!w.capture_nested_checkpoint(c,true,child,link,512u));
            ++c.inst_count;
            assert(!w.nested_frame_held(c,true,child,link,512u,256u));
            assert(!w.nested_frame_held(c,true,child,link,512u,257u));
            assert(w.nested_frame_held_after_checkpoint(c,true,child,link,512u,1u));
            assert(!w.nested_frame_held_after_checkpoint(c,true,child,link,512u,0u));
            assert(!w.nested_frame_held_after_checkpoint(c,true,child,link,512u,37u));
            assert(!w.nested_frame_held_after_checkpoint(c,true,child,link,516u,1u));
            assert(!w.nested_frame_held_after_checkpoint(c,true,child,link+4u,512u,1u));
            if(fault==30)c.mmu.write32(Sp-16,1u);
            if(fault==31)c.mmu.write32(Sp-28,link+4u);
            if(fault==32)c.mmu.write32(Sp+4,0u);
            if(fault==33)c.gpr[1]+=8u;
            if(fault==34)c.inst_count+=1u;
            if(fault==35)c.in_callback=true;
            if(fault==36)c.inst_count-=2u;
            assert(w.nested_frame_held_after_checkpoint(c,fault!=37,child,link,512u,1u)==(fault==27));
        }
    }
}
int main(){for(unsigned i=0;i<=37;++i)trial(i);std::cout<<"POST_STM_SC_ENTRY_TEST cases=38 original_execution=0\n";}
