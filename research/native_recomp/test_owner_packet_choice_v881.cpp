#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "owner_callback_prefix.h"
#include "wii_callback_prefix_v800.h"
#include "wii_handler_suffix_guard_v868.h"
#include "wii_postack_os_leaf_v703.h"
#include "wii_si_transfer_choice_v878.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
constexpr uint32_t Stack=0x80022000u,Low=Stack-0x400u,High=Stack+0x100u,MSR=0x32u;
static std::array<uint32_t,32> gp{};
static std::array<uint32_t,(High-Low)/4> stack{};
static uint32_t lr=0,ctr=0,xer=0,cr=0,next=H;
static uint64_t tick=100;
static unsigned entries=0,visits=0,outer=0,writes=0;
static bool corrupt=false;
static constexpr auto observed_prefix=[]{
    std::array<uint32_t,(Resume-C)/4u+1u> result{};
    for(unsigned i=0;i<result.size();++i)result[i]=prefix_words[i];
    return result;
}();
static undercover::wii::CallbackPrefixWitness<observed_prefix.size(),save_words.size()> witness(C,S,observed_prefix,save_words);
static constexpr auto continuation=[]{
    std::array<undercover::wii::HandlerSuffixLabel,after_save_words.size()> rows{};
    for(unsigned i=0;i<rows.size();++i){
        const uint32_t pc=Resume+4u*i;const bool call=pc==DisableCall;
        rows[i]={pc,after_save_words[i],call?2u:0u,call?1u:0u};
    }
    return rows;
}();
static undercover::wii::HandlerSuffixGuard guard;
static undercover::wii::PostAckOsLeaf leaf({DisableCall,D,D+4u*uint32_t(disable_words.size()),after_save_words.back(),1u});
static bool saved=false,disabled=false;
static undercover::wii::SiTransferChoice choice;
static unsigned trial=0;
static bool open_lane=false;
static uint32_t packet_addr=0,seed_addr=0;
static unsigned packet_reads=0,branch_visits=0,load_visits=0;
static std::string seed_path;
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V881_PREFIX_FAULT kind="<<kind<<" line="<<line
      <<" entries="<<entries<<" visits="<<visits<<" writes="<<writes<<" choice="<<choice.failure()<<" memory="<<choice.memory_failure()<<" packet_reads="<<packet_reads<<" branches="<<branch_visits<<" boundary="<<choice.boundary()<<std::endl;
    std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static uint32_t pack(CPUContext& c){
    uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
    return v;
}
static void store(uint32_t a,uint32_t v){
    need((a>=Low&&a<High)&&!(a&3u));
    stack[(a-Low)/4]=v;++writes;
}
static void state(CPUContext& c){
    need(c.gpr==gp&&c.lr==lr&&c.ctr==ctr&&c.xer==xer&&pack(c)==cr&&
        c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    for(unsigned i=0;i<stack.size();++i){
        if(c.mmu.read32(Low+4*i)!=stack[i]){
            if(corrupt&&next==Resume){
                std::cout<<"V881_PREFIX_REFUSAL saved_word_corruption=1"<<std::endl;std::_Exit(126);
            }
            fail(2);
        }
    }
}
static void reference(uint32_t pc,uint32_t w){
    const unsigned op=w>>26,xo=(w>>1)&1023,rd=(w>>21)&31,ra=(w>>16)&31,rb=(w>>11)&31;
    const uint32_t d=((w&0xffffu)^0x8000u)-0x8000u;
    next=pc+4;
    if(op==36||op==37){
        const uint32_t a=(ra?gp[ra]:0u)+d;
        store(a,gp[rd]);if(op==37)gp[ra]=a;
    }else if(op==14)gp[rd]=(ra?gp[ra]:0u)+d;
    else if(op==31&&xo==339){need((ra|(rb<<5))==8u);gp[rd]=lr;}
    else if(op==31&&xo==444)gp[ra]=gp[rd]|gp[rb];
    else if(w==0x60000000u){}
    else if(op==18&&(w&3u)==1u){
        lr=pc+4;next=pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u);
        need((pc==H&&next==C)||(pc==SaveCall&&next==S));
    }else if(w==0x4e800020u){need(pc==S+4u*(save_words.size()-1u)&&lr==Resume);next=lr;}
    else fail(3);
}
static unsigned packet_section(uint32_t a){
    if((a&3u)||a==0x80619a60u||a>=Low&&a<High)return 0;
    unsigned index=0,found=0;
    for(auto s:PacketDataSpans){
        ++index;
        if(a>=s.lo&&uint64_t(a)+4u<=s.hi){if(found)return 0;found=index;}
    }
    return found;
}
static bool packet_address(uint32_t a){return packet_section(a)!=0u;}
static unsigned seed_section=0;
static bool compared=false;
static void packet_observe(CPUContext& c,uint32_t pc,uint32_t w){
    if(w>>26==16u)++branch_visits;
    if(pc==PacketCompare){
        need(packet_reads==1u&&!compared&&c.gpr[(w>>16)&31u]==(open_lane?0xffffffffu:0u));
        compared=true;return;
    }
    if(pc!=PacketProbe)return;
    need(!packet_reads&&!packet_addr&&!compared&&w>>26==32u);
    const unsigned ra=(w>>16)&31u;
    packet_addr=(ra?c.gpr[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
    const unsigned section=packet_section(packet_addr);
    need(section&&c.mmu.get_ptr(packet_addr)&&c.mmu.get_ptr(packet_addr+3u));
    need(c.mmu.read32(packet_addr)==(open_lane?0xffffffffu:0u));
    if(open_lane)need(packet_addr==seed_addr&&section==seed_section);
    ++packet_reads;++load_visits;
}

namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick);
    need(c.mmu.read32(pc)==w);
    ++visits;need(visits<=128);
    if(disabled){
        packet_observe(c,pc,w);need(choice.before(c,pc,w));
        if(choice.boundary()){
            need(packet_reads==1u&&packet_addr&&compared&&branch_visits&&choice.boundary()==(open_lane?4u:3u));
            if(!open_lane){
                std::ofstream f(seed_path,std::ios::out|std::ios::trunc);
                need(bool(f));f<<packet_addr<<' '<<packet_section(packet_addr)<<'\n';f.close();need(bool(f));
            }
            std::cout<<"V881_OWNER_PACKET_CHOICE trial="<<trial<<" free="<<unsigned(open_lane)
                <<" next="<<choice.boundary()<<" visits="<<choice.visits()<<" original_disable_return=1 call_executed=0 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
        }
        return;
    }
    if(saved){
        if(pc==DisableResume){
            need(leaf.returned(c,pc)&&leaf.visits()==5u&&leaf.msr_writes()==1u&&c.gpr[3]==0u&&c.msr==MSR&&entries==4u&&outer==1u);
            disabled=true;packet_observe(c,pc,w);need(choice.start(c,choice_rows,pc)&&choice.before(c,pc,w)&&!choice.boundary());return;
        }
        if(pc>=D&&pc<D+4u*disable_words.size()){need(leaf.before(c,pc,w));return;}
        need(pc==next&&guard.before(c,pc,w,pc==DisableCall?2u:0u,pc==DisableCall?1u:0u));
        next=pc+4u;
        if(pc==DisableCall)need(leaf.start(c,pc,w));
        return;
    }
    need(pc==next);
    if(pc==Resume&&corrupt){
        const uint32_t a=gp[SaveBase]+uint32_t(SaveDisp);
        c.mmu.write32(a,c.mmu.read32(a)^1u);
    }
    if(pc==H)need(witness.start_direct(c,pc,w,true,true));
    else if(pc==Resume&&corrupt)need(!witness.before(c,pc,w,true)&&witness.failure()==3u);
    else need(witness.before(c,pc,w,true));
    state(c);
    if(pc==Resume){
        need(!corrupt&&entries==3&&outer==1&&writes==save_words.size()+1u&&visits==observed_prefix.size()+save_words.size()+1u&&witness.stage()==6u&&witness.writes()==writes&&witness.visits()+1u==visits);
        saved=true;need(guard.start(c,continuation,pc)&&guard.before(c,pc,w,pc==DisableCall?2u:0u,pc==DisableCall?1u:0u));
        next=pc+4u;if(pc==DisableCall)need(leaf.start(c,pc,w));return;
    }
    reference(pc,w);
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,4> order{H,C,S,D};
    need(c.pc==pc&&entries<order.size()&&pc==order[entries]);
    // The pinned dispatcher increments inst_count once before the first
    // function entry. Subsequent direct calls do not re-enter the dispatcher.
    if(entries==0){need(outer==1&&c.inst_count==tick+1u);++tick;}
    else if(pc==D)need(c.inst_count==tick&&saved&&leaf.entry(pc,c));
    else need(c.inst_count==tick&&witness.entry(c,pc,true));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){need(!outer&&!visits&&c.pc==H&&c.inst_count==tick);++outer;return false;}
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
    need(argc==4);const std::string mode=argv[1];need(mode=="discover"||mode=="open"||mode=="corrupt");corrupt=mode=="corrupt";open_lane=mode=="open";seed_path=argv[3];
    trial=unsigned(std::stoul(argv[2]));need(trial<8);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller_words);put(C,prefix_words);put(S,save_words);put(D,disable_words);for(auto a:guard_roots)put(a,guard_words);
    for(unsigned i=0;i<stack.size();++i){stack[i]=0xdeadbeefu^(trial*0x9e3779b9u+i);c.mmu.write32(Low+4*i,stack[i]);}
    for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    c.gpr[1]=Stack;c.gpr[2]=0x80025000u;c.gpr[13]=0x8070e8e0u;c.gpr[3]=trial%4;
    // Synthetic caller data, not a forced original branch or fabricated device result.
    c.gpr[4]=Stack+0x80u;c.gpr[5]=1u;c.gpr[6]=Stack+0x90u;c.gpr[7]=3u;c.gpr[8]=H;c.gpr[9]=0;c.gpr[10]=(trial&4u)?100u:0u;
    c.mmu.write8(Stack+0x80u,0u);stack[(Stack+0x80u-Low)/4u]&=0x00ffffffu;
    c.mmu.write32(0x80619a60u,0xffffffffu);
    if(open_lane){
        std::ifstream f(seed_path);uint64_t a=0;need(bool(f>>a>>seed_section)&&a<=UINT32_MAX&&seed_section);f>>std::ws;need(f.eof());
        seed_addr=uint32_t(a);need(packet_address(seed_addr)&&packet_section(seed_addr)==seed_section&&c.mmu.read32(seed_addr)==0u);c.mmu.write32(seed_addr,0xffffffffu);
    }
    gp=c.gpr;
    for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
    cr=pack(c);ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
    c.pc=H;lr=c.lr=0x80007000u;c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=tick;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    run_game(c);fail(8);
}catch(...){fail(8);}
