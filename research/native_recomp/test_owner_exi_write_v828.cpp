#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_exi_write.h"
#include "wii_exi_profile_v501.h"
#include "wii_sram_write_witness_v818.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
constexpr uint32_t ExiState=0x806f1560u,Buffer=0x80025000u;
constexpr uint32_t Stack=0x80022000u,Low=Stack-0x800u,High=Stack+0x100u,MSR=0x32u;
static ExiController* controller=nullptr;
static ExiMxDevice* mx_device=nullptr;
static ExiEndpointScheduler* scheduler=nullptr;
static SramWriteWitness witness;
static ExiMxDevice::Sram seed{},desired{};
static uint32_t pi_mask=0xf8u;
static unsigned reads=0,writes=0,polls=0,imm_calls=0,imm_returns=0,sync_calls=0,sync_returns=0,complete_count=0,revision_reads=0;
static bool backward=false,delayed=false,bad_payload=false;
struct Frame{uint32_t root,ret;std::array<uint32_t,32> gpr;uint32_t cr,msr;};
static std::array<Frame,16> frames{};
static unsigned depth=0,visits=0,entries=0;
static uint32_t next=0,entry_due=0;
static uint64_t tick=100;
static bool returned=false;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V828_EXI_FAULT kind="<<kind<<" line="<<line<<" depth="<<depth<<" visits="<<visits<<" entries="<<entries
        <<" imm="<<imm_calls<<" imm_return="<<imm_returns<<" sync="<<sync_calls<<" sync_return="<<sync_returns<<" completed="<<complete_count
        <<" reads="<<reads<<" writes="<<writes<<" polls="<<polls<<" witness="<<witness.failure()<<std::endl;std::_Exit(126);
}
static void need(bool b,const std::source_location l=std::source_location::current()){if(!b)fail(1,l.line());}
static void advance(){
    const auto q=controller->pending(0);const auto before=scheduler->completed();
    scheduler->advance(tick);
    if(scheduler->completed()!=before){
        need(q.has_value()&&scheduler->completed()==before+1u&&++complete_count==scheduler->completed());
        if(!witness.record(*q,*controller,*mx_device)){
            if(bad_payload&&complete_count==2u&&witness.failure()==4u){
                std::cout<<"V828_EXI_REFUSAL payload=1 completed=2"<<std::endl;std::_Exit(126);
            }
            fail(2);
        }
    }
}
static uint32_t pack(CPUContext& c){uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
static bool contains(uint32_t addr,unsigned n,uint32_t lo,uint32_t hi){return n&&addr>=lo&&uint64_t(addr)+n<=hi;}
static bool abi(CPUContext& c,const Frame& f){
    if(c.gpr[1]!=f.gpr[1]||c.gpr[2]!=f.gpr[2]||c.gpr[13]!=f.gpr[13]||(pack(c)&0x00fff000u)!=f.cr||c.msr!=f.msr)return false;
    for(unsigned i=14;i<32;++i)if(c.gpr[i]!=f.gpr[i])return false;
    return true;
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
        if(n==4u&&(p==0x0c003004u||(p>=0x0d006800u&&p<0x0d00683cu&&!(p&3u))))return;
        const bool revision=depth>0&&frames[depth-1].root==Revision&&op==32u&&n==4u&&a==RevisionRead;
        if(revision){need(ExiDiConfigBinding::active());return;}
        need(contains(a,n,Low,High)||contains(a,n,Buffer,Buffer+48u)||contains(a,n,ExiState,ExiState+0x100u)||contains(a,n,0x800000c0u,0x800000d0u)||contains(a,n,0x80003000u,0x80003200u));
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
    for(const auto& r:roots)if(r.address==a)return r;
    fail(3);
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u);
    need(!entry_due&&pc==next&&c.mmu.read32(pc)==w&&++visits<=12000u);backward=false;
    advance();
    if(delayed&&visits==2048u){
        need(imm_returns==1&&sync_calls==1&&sync_returns==0&&controller->pending(0)&&complete_count==0&&mx_device->sram()==seed&&!mx_device->dirty());
        std::cout<<"V828_EXI_REFUSAL timeout=1 original_sync_pending=1 completed=0"<<std::endl;std::_Exit(126);
    }
    if(returned){
        need(depth>1&&c.pc==pc&&c.lr==pc);
        const auto& f=frames[depth-1];need(abi(c,f));
        if(f.root==Imm){
            need(c.gpr[3]==1u&&c.mmu.read32(ExiState+12u)==0x16u&&++imm_returns==imm_calls);
            need(controller->selection_epoch(0)==1u&&complete_count<=imm_returns&&complete_count+1u>=imm_returns);
        }
        if(f.root==Sync){
            need(c.gpr[3]==1u&&c.mmu.read32(ExiState+12u)==0x14u&&!controller->pending(0)&&++sync_returns==sync_calls&&complete_count==sync_returns);
        }
        --depth;returned=false;
    }
    if(pc==Stop){
        need(depth==1&&imm_calls==12&&imm_returns==12&&sync_calls==12&&sync_returns==12&&complete_count==12&&witness.stage()==3&&witness.bytes()==44u&&witness.completed()==12u&&revision_reads==12u);
        need(!controller->pending(0)&&mx_device->sram()==desired&&mx_device->dirty());
        // Fixture-owned chip deselection, after all original transfers.
        controller->write(0,0,8u);need(witness.finish(*controller,*mx_device));
        need(c.mmu.read8(Buffer-1u)==0xa7&&c.mmu.read8(Buffer+48u)==0xa7);
        for(unsigned i=0;i<44;++i)need(c.mmu.read8(Buffer+4u+i)==desired[20u+i]);
        std::cout<<"V828_OWNER_EXI_WRITE original_imm=12 original_sync=12 transfers=12 bytes=44 payload=1 abi=1 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
    const auto& r=root_at(frames[depth-1].root);
    need(contains(pc,4,r.address,r.address+4u*uint32_t(r.words.size()))&&r.words[(pc-r.address)/4u]==w);
    memory(c,w);
    next=pc+4;
    const auto op=w>>26,xo=(w>>1)&1023u;
    if(op==18u&&(w&3u)==1u){
        const auto dst=target(pc,w);root_at(dst);need(depth<frames.size());
        frames[depth++]={dst,pc+4u,c.gpr,pack(c)&0x00fff000u,c.msr};
        if(dst==RestoreAlias){
            // Restore aliases intentionally change the nonvolatile GPRs.
            // Snapshot the stack source BEFORE the translated loads.
            for(unsigned i=0;i<AliasCount;++i){const uint32_t a=c.gpr[RestoreBase]+uint32_t(AliasDisp)+4u*i;need(contains(a,4,Low,High));frames[depth-1].gpr[32u-AliasCount+i]=c.mmu.read32(a);}
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
    need(op!=17u&&!(op==19u&&(xo==16u||xo==50u||xo==528u))&&(!(op==31u&&xo==146u)||r.address==D||r.address==R));
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(c.pc==pc);
    if(!entries){need(pc==H&&c.inst_count==tick+1u&&depth==1);++tick;}
    else{
        need(entry_due==pc&&c.inst_count==tick&&depth>=2&&c.lr==frames[depth-1].ret);
        entry_due=0;
    }
    ++entries;
    if(pc==Imm){
        need(depth==2&&imm_calls==sync_returns&&++imm_calls<=12u&&c.gpr[3]==0u&&c.gpr[4]==Buffer+4u*(imm_calls-1u)&&c.gpr[5]==4u&&c.gpr[6]==1u&&c.gpr[7]==0u);
        need(c.mmu.read32(ExiState+12u)==0x14u&&!controller->pending(0)&&complete_count==imm_calls-1u);
    }
    if(pc==Sync){
        need(depth==2&&++sync_calls==imm_returns&&c.gpr[3]==0u&&c.mmu.read32(ExiState+12u)==0x16u);
    }
    if(pc==ConsoleGuard)fail(3);
}
bool process_pending_callbacks(CPUContext& c){
    if(!entries){need(!visits&&c.pc==H&&c.inst_count==tick);return false;}
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
        need(depth>0&&frames[depth-1].root==Revision&&++revision_reads<=12u);
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
        const unsigned off=a-0x0d006800u;need(off<20u&&off%20u!=4u&&off%20u!=8u);
        if(off==0)need((v&0x380u)==0x100u);
        controller->write(off/20u,off%20u,v);return;
    }
    fail(7);
}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==3);const std::string mode=argv[1];need(mode=="valid"||mode=="delayed"||mode=="bad-payload");
    delayed=mode=="delayed";bad_payload=mode=="bad-payload";
    const unsigned trial=unsigned(std::stoul(argv[2]));need(trial<4u);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    std::atomic<uint32_t> cause{0x100u};WiiIrqBanks banks(cause);ExiController exi(banks);controller=&exi;
    for(unsigned i=0;i<64;++i)seed[i]=uint8_t(i*17u+trial+7u);
    desired=seed;desired[48u+2u*trial]^=0x5au;desired[49u+2u*trial]^=0xa5u;
    ExiMxDevice mx(seed,[]{return 0u;});ExiIdEndpoint id(0u);mx_device=&mx;
    ExiEndpointScheduler sched(exi,mx,id,delayed?100000u:32u+trial*24u);scheduler=&sched;
    exi.write(0,0,0x2000u);need(witness.begin(exi,mx,20u,desired));
    exi.write(0,0,0x2130u);
    for(const auto& r:roots){uint32_t a=r.address;for(auto w:r.words){c.mmu.write32(a,w);a+=4u;}}
    for(uint32_t a=Low;a<High;a+=4u)c.mmu.write32(a,a^0xdeadbeefu);
    for(uint32_t a=ExiState;a<ExiState+0x100u;a+=4u)c.mmu.write32(a,0);
    c.mmu.write32(ExiState+12u,0x14u);
    ExiDiConfigBinding di(1u); // same explicit DI configuration as V60/V501
    c.mmu.write32(0x800000c4u,0xfffffff0u);c.mmu.write32(0x800000c8u,0);
    c.mmu.write32(Buffer,0xa0000600u);
    for(unsigned i=0;i<44;++i)c.mmu.write8(Buffer+4u+i,desired[20u+i]);
    if(bad_payload)c.mmu.write8(Buffer+4u,c.mmu.read8(Buffer+4u)^1u);
    c.mmu.write8(Buffer-1u,0xa7);c.mmu.write8(Buffer+48u,0xa7);
    for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u;
    c.gpr[1]=Stack;c.gpr[2]=0x80026000u;c.gpr[13]=0x8070e8e0u;c.gpr[14]=Buffer;
    c.pc=next=H;c.lr=0x80007000u;c.ctr=0x12345678u;c.xer=0x80000000u;
    c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=tick;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    frames[0]={H,c.lr,c.gpr,pack(c)&0x00fff000u,c.msr};depth=1;
    run_game(c);fail(8);
}catch(...){fail(8);}
