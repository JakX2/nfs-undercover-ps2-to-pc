#pragma once
#include "wii_exi_profile_v501.h"
#include "wii_sram_write_witness_v818.h"
namespace joined {
using nwii::runtime::CPUContext;
using namespace undercover::wii;
using namespace write_roots;
constexpr uint32_t ExiState=0x806f1560u;
static ExiController* controller=nullptr;
static ExiMxDevice* mx_device=nullptr;
static ExiEndpointScheduler* scheduler=nullptr;
static SramWriteWitness witness;
static ExiMxDevice::Sram desired{};
static unsigned imm_calls=0,imm_returns=0,sync_calls=0,sync_returns=0,immex_calls=0,immex_returns=0,deselects=0,deselect_returns=0,complete_count=0,revision_reads=0;
static uint32_t pi_mask=0xf8u;
static unsigned locks=0,lock_returns=0,mask_calls=0,reads=0,writes=0,polls=0,selects=0,select_returns=0;
static bool backward=false;
constexpr uint32_t Stack=0x80022000u,Low=Stack-0x800u,High=Stack+0x100u,Sram=0x806f52c0u,MSR=0x32u;
constexpr uint32_t Wireless=48u; // public extended SRAM layout (20 + 24 + 4)
struct Frame{uint32_t root,ret;std::array<uint32_t,32> gpr;uint32_t cr,msr;};
static std::array<Frame,16> frames{};
static unsigned depth=0,visits=0,entries=0,unlocks=0,disables=0,restores=0,channel=0;
static unsigned lane=0,exi_unlocks=0,exi_unlock_returns=0,sram_returns=0;
static uint16_t initial_id=0,new_id=0;
static std::array<uint8_t,64> initial{};
static uint32_t next=0,entry_due=0,outer_pc=0;
static uint64_t tick=100;
static bool returned=false,corrupt=false,active=false;
static uint32_t caller_sp=0;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V816_WIRELESS_FAULT kind="<<kind<<" line="<<line<<" lane="<<lane<<" depth="<<depth
        <<" visits="<<visits<<" entries="<<entries<<" unlocks="<<unlocks<<" disables="<<disables<<" restores="<<restores<<std::endl;
    std::cout<<"V819_LOCK_DIAG lock="<<locks<<" returned="<<lock_returns<<" masks="<<mask_calls<<" reads="<<reads<<" writes="<<writes<<" polls="<<polls<<std::endl;
    std::cout<<"V825_SELECT_DIAG selected="<<selects<<" returned="<<select_returns<<std::endl;
    std::cout<<"V835_WRITE_DIAG imm="<<imm_calls<<" imm_return="<<imm_returns<<" sync="<<sync_calls<<" sync_return="<<sync_returns<<" extended="<<immex_calls<<" deselect="<<deselects<<" completed="<<complete_count<<" witness="<<witness.failure()<<std::endl;
    std::cout<<"V837_RETURN_DIAG exi_unlock="<<exi_unlocks<<" exi_return="<<exi_unlock_returns<<" sram_return="<<sram_returns<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)fail(1,l.line());}
static void advance(){
    const auto q=controller->pending(0);const auto old=scheduler->completed();
    scheduler->advance(tick);
    if(scheduler->completed()!=old){
        need(q.has_value()&&scheduler->completed()==old+1u&&++complete_count==scheduler->completed());
        need(witness.record(*q,*controller,*mx_device));
    }
}
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
    if(n){
        const uint32_t p=a&0x3fffffffu;
        if(depth&&frames[depth-1].root==Revision&&op==32u&&n==4u&&a==RevisionRead){need(ExiDiConfigBinding::active());return;}
        if(n==4u&&(p==0x0c003004u||(p>=0x0d006800u&&p<0x0d00683cu&&!(p&3u))))return;
        need(contains(a,n,Low,High)||contains(a,n,Sram,Sram+80u)||contains(a,n,ExiState,ExiState+0x100u)||contains(a,n,0x800000c0u,0x800000d0u));
        for(unsigned i=0;i<n;++i)need(c.mmu.get_ptr(a+i));
    }
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
    for(const auto& r:all_roots)if(r.address==a)return r;
    fail(3);
}

void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u);
    need(!entry_due&&pc==next&&c.mmu.read32(pc)==w&&++visits<=12000u);backward=false;advance();
    if(returned){
        need(depth>1&&c.pc==pc&&c.lr==pc);
        if(corrupt&&depth==2){c.gpr[14]^=1u;need(!abi(c,frames[depth-1]));std::cout<<"V826_JOIN_REFUSAL abi=1"<<std::endl;std::_Exit(126);}
        const auto& f=frames[depth-1];need(abi(c,f));
        if(f.root==L){need(c.gpr[3]==1u&&c.mmu.read32(ExiState+12u)==0x10u&&!controller->pending(0));++lock_returns;}
        if(f.root==Select){need(c.gpr[3]==1u&&c.mmu.read32(ExiState+12u)==0x14u&&!controller->pending(0)&&(controller->read(0,0)&0x3f0u)==0x130u&&controller->selection_epoch(0)==1);++select_returns;}
        if(f.root==Imm){need(c.gpr[3]==1u&&c.mmu.read32(ExiState+12u)==0x16u&&++imm_returns==imm_calls);}
        if(f.root==Sync){need(c.gpr[3]==1u&&c.mmu.read32(ExiState+12u)==0x14u&&!controller->pending(0)&&++sync_returns==sync_calls&&complete_count==sync_returns);}
        if(f.root==ImmEx){need(c.gpr[3]==1u&&++immex_returns==1u&&complete_count==12u&&witness.stage()==3u&&witness.bytes()==44u);}
        if(f.root==Deselect){need(c.gpr[3]==1u&&++deselect_returns==1u&&c.mmu.read32(ExiState+12u)==0x10u&&witness.finish(*controller,*mx_device));}
        if(f.root==ExiUnlock){need(c.gpr[3]==1u&&++exi_unlock_returns==1u&&c.mmu.read32(ExiState+12u)==0u&&mask_calls==2u&&!controller->pending(0)&&witness.stage()==4u);}
        if(f.root==write_roots::U){need(++sram_returns==1u&&c.gpr[3]==1u&&c.mmu.read32(Sram+64u)==64u&&c.mmu.read32(Sram+72u)==0u&&c.mmu.read32(Sram+76u)==1u);}
        --depth;returned=false;
    }
    if(pc==outer_pc+4u){
        need(depth==1&&unlocks==1&&sram_returns==1u&&disables==restores&&c.gpr[1]==caller_sp);
        need(c.mmu.read32(Sram+64u)==64u&&c.mmu.read32(Sram+68u)==0&&c.mmu.read32(Sram+72u)==0&&c.mmu.read32(Sram+76u)==1);
        if(lane==2){
            need(exi_unlocks==1u&&exi_unlock_returns==1u&&locks==1u&&lock_returns==1u&&select_returns==1u&&deselect_returns==1u&&mask_calls==2u);
            need(imm_returns==12u&&sync_returns==12u&&revision_reads==12u&&witness.stage()==4u&&witness.completed()==12u&&witness.bytes()==44u);
            need(!controller->pending(0)&&!(controller->read(0,0)&0x380u)&&mx_device->sram()==desired&&mx_device->dirty()&&c.mmu.read32(ExiState+12u)==0u);
            payload(c,true);
            std::cout<<"V838_OWNER_CALLBACK_WRITE original_time_return=1 original_setter_return=1 original_unlock=1 bytes=44 payload=1 abi=1 callback_return=0 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
        }
        need(disables==1u&&!exi_unlocks&&!exi_unlock_returns);
        payload(c,false);need(!complete_count&&!mx_device->dirty()&&mx_device->sram()==initial&&!witness.stage());
        need(lane==1u&&initial_id==new_id);
        std::cout<<"V826_OWNER_CALLBACK_WIRELESS original_time_return=1 original_setter_return=1 abi=1 unchanged=1 exi=0 callback_return=0 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
    const auto& r=root_at(frames[depth-1].root);
    need(contains(pc,4,r.address,r.address+4u*uint32_t(r.words.size()))&&r.words[(pc-r.address)/4u]==w);
    memory(c,w);
    next=pc+4;
    const auto op=w>>26,xo=(w>>1)&1023u;
    if(op==18u&&(w&3u)==1u){
        const auto dst=target(pc,w);root_at(dst);need(depth<frames.size());
        frames[depth++]={dst,pc+4u,c.gpr,pack(c)&0x00fff000u,c.msr};
        for(auto rule:restore_rules)if(dst==rule.root){
            for(unsigned i=0;i<rule.count;++i){
                const uint32_t a=c.gpr[rule.base]+uint32_t(rule.disp)+4u*i;
                need(contains(a,4,Low,High));frames[depth-1].gpr[32u-rule.count+i]=c.mmu.read32(a);
            }
        }
        entry_due=next=dst;return;
    }
    if(w==0x4e800020u){need(depth>1&&c.lr==frames[depth-1].ret);returned=true;next=c.lr;return;}
    if(op==16u||op==18u){
        need(!(w&3u));const uint32_t dst=target(pc,w);
        need(contains(dst,4,r.address,r.address+4u*uint32_t(r.words.size())));
        backward=dst<=pc;
        if(op==18u||taken(c,w))next=dst;
        return;
    }
    // No queued callback may dispatch until its queue ownership and target are verified.
    if(r.address==ExiUnlock&&w==0x4e800421u)fail(3);
    need(op!=17u&&!(op==19u&&(xo==16u||xo==50u||xo==528u))&&(!(op==31u&&xo==146u)||r.address==D||r.address==R));
}
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc);
    need(active&&entry_due==pc&&c.inst_count==tick&&depth>=2&&c.lr==frames[depth-1].ret);
    entry_due=0;
    ++entries;
    if(pc==D)++disables;
    if(pc==R)++restores;
    if(pc==write_roots::U){
        need(++unlocks==1&&c.gpr[3]==unsigned(lane==2)&&c.gpr[4]==20u);
        need(c.mmu.read32(Sram+72u)==1u&&c.mmu.read32(Sram+64u)==64u);
        payload(c,lane==2);
    }
    if(pc==L){
        need(lane==2&&depth==4&&unlocks==1&&disables==1&&restores==0&&++locks==1);
        need(c.gpr[3]==0u&&c.gpr[4]==1u&&c.gpr[5]&&!(c.gpr[5]&3u)&&c.gpr[5]>=0x80000000u&&c.gpr[5]<0x81800000u);
        need(c.mmu.read32(Sram+64u)==20u&&c.mmu.read32(Sram+72u)==1u&&c.mmu.read32(ExiState+12u)==0);
        payload(c,true);
    }
    if(pc==MaskHelper){need(c.gpr[3]==0u&&c.gpr[4]==ExiState);++mask_calls;}
    if(pc==Select){
        need(lane==2&&depth==4&&unlocks==1&&locks==1&&lock_returns==1&&mask_calls==1&&++selects==1);
        need(c.gpr[3]==0u&&c.gpr[4]==1u&&c.gpr[5]==3u&&c.mmu.read32(ExiState+12u)==0x10u);
        payload(c,true);need(!controller->pending(0)&&!(controller->read(0,0)&0x380u)&&witness.begin(*controller,*mx_device,20u,desired));
    }
    if(pc==Imm){
        need(lane==2&&select_returns==1&&imm_calls==sync_returns&&++imm_calls<=12u);
        need(c.gpr[3]==0u&&c.gpr[5]==4u&&c.gpr[6]==1u&&c.gpr[7]==0u&&!controller->pending(0));
        if(imm_calls==1u){
            need(depth==4&&contains(c.gpr[4],4,Low,High)&&c.mmu.read32(c.gpr[4])==0xa0000600u);
        }else need(immex_calls==1u&&c.gpr[4]==Sram+20u+4u*(imm_calls-2u));
        need(c.mmu.read32(ExiState+12u)==0x14u&&complete_count==imm_calls-1u);
    }
    if(pc==Sync){
        need(c.gpr[3]==0u&&++sync_calls==imm_returns&&c.mmu.read32(ExiState+12u)==0x16u);
    }
    if(pc==ImmEx){
        need(++immex_calls==1u&&sync_returns==1u&&complete_count==1u&&witness.stage()==2u);
        need(c.gpr[3]==0u&&c.gpr[4]==Sram+20u&&c.gpr[5]==44u&&c.gpr[6]==1u);
    }
    if(pc==Deselect){
        need(++deselects==1u&&immex_returns==1u&&c.gpr[3]==0u&&complete_count==12u&&witness.stage()==3u&&mx_device->sram()==desired);
    }
    if(pc==ExiUnlock){
        need(lane==2&&depth==4&&select_returns==1&&deselect_returns==1&&++exi_unlocks==1u);
        need(c.gpr[3]==0u&&c.mmu.read32(ExiState+12u)==0x10u&&imm_returns==12u&&sync_returns==12u&&revision_reads==12u&&witness.stage()==4u&&witness.completed()==12u&&witness.bytes()==44u);
        need(!controller->pending(0)&&!(controller->read(0,0)&0x380u)&&mx_device->sram()==desired&&mx_device->dirty());
        payload(c,true);
    }
    if(std::find(exi_guards.begin(),exi_guards.end(),pc)!=exi_guards.end())fail(3);
}
bool process_pending_callbacks(CPUContext& c){
    need(active&&entries);
    need(backward&&c.inst_count==tick&&++polls<=4096u);backward=false;return false;
}
bool handle_syscall(CPUContext&){fail(4);}
void interpret_step(CPUContext&){fail(5);}void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(5);}
void note_null_call(uint32_t,uint32_t){fail(6);}void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(7);}void GX_WGPIPE_Write16(uint16_t){fail(7);}void GX_WGPIPE_Write32(uint32_t){fail(7);}
void GX_WGPIPE_WriteF32(float){fail(7);}void GX_WGPIPE_WriteF64(double){fail(7);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}
uint32_t HW_Reg_Read32(uint32_t a){
    ++reads;need(reads<=4096&&controller);
    if(a==0x0c003004u)return pi_mask;
    if(a==(RevisionRead&0x3fffffffu)){
        need(depth&&frames[depth-1].root==Revision&&++revision_reads<=12u);
        const auto v=ExiDiConfigBinding::read32(a);need(v.has_value()&&*v==1u);return *v;
    }
    if(a>=0x0d006800u&&a<0x0d00683cu&&!(a&3u)){const unsigned off=a-0x0d006800u;return controller->read(off/20u,off%20u);}
    fail(7);
}
void HW_Reg_Write16(uint32_t,uint16_t){fail(7);}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    ++writes;need(writes<=512&&controller);
    if(a==0x0c003004u){pi_mask=v;return;}
    if(a>=0x0d006800u&&a<0x0d00683cu&&!(a&3u)){
        const unsigned off=a-0x0d006800u;
        if(off%20u==0){need(!(v&0x380u)||(off==0&&selects==1&&!deselects&&(v&0x380u)==0x100u));}
        else need(off<20u&&(off==12u||off==16u));
        controller->write(off/20u,off%20u,v);return;
    }
    fail(7);
}


void start(CPUContext& c,uint32_t pc,uint32_t target,unsigned ch,bool changed,bool bad,
           const std::array<uint8_t,64>& seed){
    need(!active&&ch<4u&&target==Setter&&c.gpr[3]==ch&&c.gpr[4]==0u);
    active=true;channel=ch;lane=changed?2u:1u;corrupt=bad;
    initial=seed;initial_id=uint16_t((unsigned(seed[48u+2u*ch])<<8)|seed[49u+2u*ch]);new_id=0;
    need((initial_id!=new_id)==changed);
    desired=seed;desired[48u+2u*ch]=desired[49u+2u*ch]=0;
    tick=c.inst_count;outer_pc=pc;caller_sp=c.gpr[1];
    frames[0]={C,c.lr,c.gpr,pack(c)&0x00fff000u,c.msr};
    frames[1]={target,pc+4u,c.gpr,pack(c)&0x00fff000u,c.msr};depth=2;
    entry_due=next=target;
    payload(c,false);
}

}
