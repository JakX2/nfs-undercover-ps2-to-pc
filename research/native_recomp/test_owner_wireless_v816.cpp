#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_wireless.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t Stack=0x80022000u,Low=Stack-0x800u,High=Stack+0x100u,Sram=0x806f52c0u,MSR=0x32u;
constexpr uint32_t Wireless=48u; // public extended SRAM layout (20 + 24 + 4)
struct Frame{uint32_t root,ret;std::array<uint32_t,32> gpr;uint32_t cr,msr;};
static std::array<Frame,8> frames{};
static unsigned depth=0,visits=0,entries=0,unlocks=0,disables=0,restores=0,channel=0;
static unsigned lane=0;
static uint16_t initial_id=0,new_id=0;
static std::array<uint8_t,64> initial{};
static uint32_t next=0,entry_due=0,outer_pc=0;
static uint64_t tick=100;
static bool returned=false,corrupt=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V816_WIRELESS_FAULT kind="<<kind<<" line="<<line<<" lane="<<lane<<" depth="<<depth
        <<" visits="<<visits<<" entries="<<entries<<" unlocks="<<unlocks<<" disables="<<disables<<" restores="<<restores<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)fail(1,l.line());}
static uint32_t pack(CPUContext& c){uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
static bool contains(uint32_t addr,unsigned n,uint32_t lo,uint32_t hi){return n&&addr>=lo&&uint64_t(addr)+n<=hi;}
static bool abi(CPUContext& c,const Frame& f){
    if(c.gpr[1]!=f.gpr[1]||c.gpr[2]!=f.gpr[2]||c.gpr[13]!=f.gpr[13]||(pack(c)&0x00fff000u)!=f.cr||c.msr!=f.msr)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=f.gpr[i])return false;
    return true;
}
static void payload(CPUContext& c,bool changed){
    for(unsigned i=0;i<64;++i){
        uint8_t v=initial[i];
        if(changed&&i==Wireless+2u*channel)v=uint8_t(new_id>>8);
        if(changed&&i==Wireless+2u*channel+1u)v=uint8_t(new_id);
        need(c.mmu.read8(Sram+i)==v);
    }
    need(c.mmu.read8(Sram-1u)==0xa7u&&c.mmu.read8(Sram+80u)==0xa7u);
}
static void memory(CPUContext& c,uint32_t w){
    const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u;
    unsigned n=0;uint32_t a=0;
    if(op>=32u&&op<=47u){
        a=(ra?c.gpr[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
        n=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
        if(op==46u||op==47u)n=4u*(32u-((w>>21)&31u));
    }else if(op==31u){
        switch(xo){
        case 23:case 55:case 151:case 183:case 534:case 662:n=4;break;
        case 87:case 119:case 215:case 247:n=1;break;
        case 279:case 311:case 343:case 375:case 407:case 439:case 790:case 918:n=2;break;
        case 20:case 150:case 533:case 597:case 661:case 725:case 535:case 567:case 599:case 631:case 663:case 695:case 727:case 759:case 983:
        case 54:case 86:case 246:case 278:case 470:case 982:case 1014:fail(3);
        default:break;
        }
        a=(ra?c.gpr[ra]:0u)+c.gpr[rb];
    }else need(op<48u&&op!=4u);
    if(n){need(contains(a,n,Low,High)||contains(a,n,Sram,Sram+80u));for(unsigned i=0;i<n;++i)need(c.mmu.get_ptr(a+i));}
}
static uint32_t target(uint32_t pc,uint32_t w){
    const uint32_t b=w>>26==16u?0xfffcu:0x03fffffcu,s=w>>26==16u?0x8000u:0x02000000u;
    return pc+(((w&b)^s)-s);
}
static bool taken(CPUContext& c,uint32_t w){
    const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
    return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));
}
static const Root& root_at(uint32_t a){
    for(const auto& r:roots)if(r.address==a)return r;
    fail(3);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u);
    need(!entry_due&&pc==next&&c.mmu.read32(pc)==w&&++visits<=320u);
    if(returned){
        need(depth>1&&c.pc==pc&&c.lr==pc);
        if(corrupt&&depth==2){c.gpr[14]^=1u;need(!abi(c,frames[depth-1]));std::cout<<"V816_WIRELESS_REFUSAL abi=1"<<std::endl;std::_Exit(126);}
        need(abi(c,frames[depth-1]));--depth;returned=false;
    }
    if(pc==outer_pc+4u){
        need(lane!=2&&depth==1&&unlocks==1&&disables==1&&restores==1&&c.gpr[1]==Stack);
        need(c.mmu.read32(Sram+64u)==64u&&c.mmu.read32(Sram+68u)==0&&c.mmu.read32(Sram+72u)==0&&c.mmu.read32(Sram+76u)==1);
        payload(c,false);
        if(lane==0)need(c.gpr[3]==initial_id);
        std::cout<<"V816_OWNER_WIRELESS_RETURN lane="<<lane<<" original_wrapper=1 unlock=1 abi=1 payload=1 exi=0 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
    const auto& r=root_at(frames[depth-1].root);
    need(contains(pc,4,r.address,r.address+4u*uint32_t(r.words.size()))&&r.words[(pc-r.address)/4u]==w);
    memory(c,w);
    next=pc+4;
    const auto op=w>>26,xo=(w>>1)&1023u;
    if(op==18u&&(w&3u)==1u){
        const auto dst=target(pc,w);root_at(dst);need(depth<frames.size());
        frames[depth++]={dst,pc+4u,c.gpr,pack(c)&0x00fff000u,c.msr};
        entry_due=next=dst;return;
    }
    if(w==0x4e800020u){need(depth>1&&c.lr==frames[depth-1].ret);returned=true;next=c.lr;return;}
    if(op==16u||op==18u){
        need(!(w&3u));const uint32_t dst=target(pc,w);
        need(contains(dst,4,r.address,r.address+4u*uint32_t(r.words.size())));
        if(op==18u||taken(c,w))next=dst;
        return;
    }
    need(op!=17u&&!(op==19u&&(xo==16u||xo==50u||xo==528u))&&(!(op==31u&&xo==146u)||r.address==D||r.address==R));
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc);
    if(!entries){need(pc==outer_pc&&c.inst_count==tick+1u&&depth==1);++tick;}
    else{
        need(entry_due==pc&&c.inst_count==tick&&depth>=2&&c.lr==frames[depth-1].ret);
        entry_due=0;
    }
    ++entries;
    if(pc==D)++disables;
    if(pc==R)++restores;
    if(pc==U){
        need(++unlocks==1&&c.gpr[3]==unsigned(lane==2)&&c.gpr[4]==20u);
        need(c.mmu.read32(Sram+72u)==1u&&c.mmu.read32(Sram+64u)==64u);
        payload(c,lane==2);
    }
    if(std::find(guards.begin(),guards.end(),pc)!=guards.end()){
        need(pc==L&&lane==2&&depth==4&&unlocks==1&&disables==1&&restores==0);
        need(c.gpr[3]==0u&&c.gpr[4]==1u&&c.gpr[5]&&!(c.gpr[5]&3u)&&c.gpr[5]>=0x80000000u&&c.gpr[5]<0x81800000u);
        need(c.mmu.read32(Sram+64u)==20u&&c.mmu.read32(Sram+72u)==1u);
        payload(c,true);
        std::cout<<"V816_OWNER_WIRELESS_CHANGED original_wrapper=1 buffer_update=1 unlock_prefix=1 exi_lock_entry=1 exi_executed=0 callback_return=0 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
}
bool process_pending_callbacks(CPUContext& c){need(!entries&&!visits&&c.pc==outer_pc&&c.inst_count==tick);return false;}
bool handle_syscall(CPUContext&){fail(4);}
void interpret_step(CPUContext&){fail(5);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(5);}
void note_null_call(uint32_t,uint32_t){fail(6);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(7);}void GX_WGPIPE_Write16(uint16_t){fail(7);}void GX_WGPIPE_Write32(uint32_t){fail(7);}
void GX_WGPIPE_WriteF32(float){fail(7);}void GX_WGPIPE_WriteF64(double){fail(7);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}uint32_t HW_Reg_Read32(uint32_t){fail(7);}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}void HW_Reg_Write32(uint32_t,uint32_t){fail(7);}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==3);const std::string mode=argv[1];need(mode=="get"||mode=="same"||mode=="changed"||mode=="corrupt");
    corrupt=mode=="corrupt";lane=mode=="same"?1u:mode=="changed"?2u:0u;
    channel=unsigned(std::stoul(argv[2]));need(channel<4);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    for(const auto& r:roots){uint32_t a=r.address;for(auto w:r.words){c.mmu.write32(a,w);a+=4u;}}
    for(uint32_t a=Low;a<High;a+=4u)c.mmu.write32(a,a^0xdeadbeefu);
    for(unsigned i=0;i<64;++i){initial[i]=uint8_t(17u*i+channel+7u);c.mmu.write8(Sram+i,initial[i]);}
    c.mmu.write8(Sram-1u,0xa7);c.mmu.write8(Sram+80u,0xa7);
    c.mmu.write32(Sram+64u,64);c.mmu.write32(Sram+68u,0);c.mmu.write32(Sram+72u,0);c.mmu.write32(Sram+76u,1);
    initial_id=uint16_t((unsigned(initial[Wireless+channel*2u])<<8)|initial[Wireless+channel*2u+1u]);
    new_id=lane==2?uint16_t(initial_id^0x55aau):initial_id;
    for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u;
    c.gpr[1]=Stack;c.gpr[2]=0x80025000u;c.gpr[13]=0x8070e8e0u;c.gpr[3]=channel;c.gpr[4]=new_id;
    c.pc=next=outer_pc=lane?H:J;c.lr=0x80007000u;c.ctr=0x12345678u;c.xer=0x80000000u;
    c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=tick;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    frames[0]={outer_pc,c.lr,c.gpr,pack(c)&0x00fff000u,c.msr};depth=1;
    run_game(c);fail(8);
}catch(...){fail(8);}
