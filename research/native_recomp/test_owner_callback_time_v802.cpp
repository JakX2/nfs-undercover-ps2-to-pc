#include "runtime/cpu_context.h"
#include "rfi_test_v708.h"
#include "wii_postack_os_leaf_v703.h"
#include "wii_callback_time_v810.h"
#include "owner_callback_time.h"
#include <array>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <source_location>
#include <string>
using nwii::runtime::CPUContext;
using namespace undercover::wii;
constexpr uint32_t Stack=0x80022000u,Low=Stack-0x400u,High=Stack+0x100u,MSR=0x32u;
static std::array<uint32_t,32> gp{};
static std::array<uint32_t,(High-Low)/4> stack{};
static uint32_t lr=0,ctr=0,xer=0,cr=0,next=H;
static uint64_t tick=100,initial_tick=100,first_upper_delta=0;
static unsigned entries=0,visits=0,outer=0,writes=0;
static bool corrupt=false,after_save=false,in_time=false,leaf_active=false,time_done=false;
static unsigned corrupt_kind=0;
static bool rollover=false;
static constexpr uint32_t Offset=0x800030d8u; // previously verified by V435 cold OS time
static uint64_t offset=0;
static unsigned offset_reads=0;
static unsigned cursor=0,time_visits=0,time_reads=0,polls=0,pending_reg=32;
static uint32_t expected_word=0;
static uint64_t tb_value=0;
static std::array<uint32_t,32> time_gp{};
static uint32_t time_cr=0;
static std::array<PostAckOsLeaf,3> leaves{PostAckOsLeaf({leaf_sites[0],D,D+4u*uint32_t(disable_words.size()),leaf_branches[0],1}),PostAckOsLeaf({leaf_sites[1],U,U+4u*uint32_t(time_words.size()),leaf_branches[1],2}),PostAckOsLeaf({leaf_sites[2],R,R+4u*uint32_t(restore_words.size()),leaf_branches[2],3})};
static CallbackTimeWitness reusable({C,C+688u,Resume,TimeCall,T,
    std::span<const uint32_t>(prefix_words).subspan((Resume-C)/4u,(TimeResume-Resume)/4u+1u),
    system_words,{{{leaf_sites[0],D,D+4u*uint32_t(disable_words.size()),leaf_branches[0],1},
    {leaf_sites[1],U,U+4u*uint32_t(time_words.size()),leaf_branches[1],2},
    {leaf_sites[2],R,R+4u*uint32_t(restore_words.size()),leaf_branches[2],3}}},Offset});
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V802_CALLBACK_FAULT kind="<<kind<<" line="<<line
      <<" entries="<<entries<<" visits="<<visits<<" writes="<<writes<<std::endl;
    std::cout<<"V810_TIME_WITNESS stage="<<reusable.stage()<<" reason="<<reusable.failure()<<" visits="<<reusable.visits()<<" cursor="<<reusable.cursor()<<std::endl;
    std::_Exit(126);
}
static void need(bool b,const std::source_location loc=std::source_location::current()){if(!b)fail(1,loc.line());}
static uint32_t pack(CPUContext& c){
    uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);
    return v;
}
static void store(uint32_t a,uint32_t v){
    need(a>=Low&&a<High&&!(a&3u));
    stack[(a-Low)/4]=v;++writes;
}
static void state(CPUContext& c){
    need(c.gpr==gp&&c.lr==lr&&c.ctr==ctr&&c.xer==xer&&pack(c)==cr&&
        c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    for(unsigned i=0;i<stack.size();++i){
        if(c.mmu.read32(Low+4*i)!=stack[i]){
            if(corrupt&&next==Resume){
                std::cout<<"V797_PREFIX_REFUSAL saved_word_corruption=1"<<std::endl;std::_Exit(126);
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
    }else if(w==0x4e800020u){need(pc==S+24&&lr==Resume);next=lr;}
    else fail(3);
}
static bool span(uint32_t a,uint32_t root,std::size_t n){return a>=root&&uint64_t(a)<uint64_t(root)+4*n;}
static void mapped_word(CPUContext& c,uint32_t addr,unsigned width,bool write){
    need(width&&addr>=0x80000000u&&uint64_t(addr)+width<=0x81800000ull);
    need(c.mmu.get_ptr(addr)&&c.mmu.get_ptr(addr+width-1u));
    if(write){
        auto overlaps=[&](uint32_t root,std::size_t n){return uint64_t(addr)<uint64_t(root)+4*n&&uint64_t(root)<uint64_t(addr)+width;};
        need(!overlaps(H,caller_words.size())&&!overlaps(C,prefix_words.size())&&!overlaps(S,save_words.size())&&
             !overlaps(T,system_words.size())&&!overlaps(D,disable_words.size())&&!overlaps(U,time_words.size())&&!overlaps(R,restore_words.size()));
    }
    if(in_time&&!write&&(addr<Low||addr>=High)){
        need(width==4u&&(addr==Offset||addr==Offset+4u));
        need(c.mmu.read32(addr)==uint32_t(addr==Offset?offset>>32:offset));
        ++offset_reads;
    }
}
static void memory_guard(CPUContext& c,uint32_t w){
    unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u,width=0;
    bool write=false;
    uint32_t addr=0;
    if(op>=32u&&op<=47u){
        addr=(ra?c.gpr[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
        width=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
        if(op==46u||op==47u)width=4u*(32u-((w>>21)&31u));
        write=op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u;
    }else if(op==31u){
        switch(xo){
        case 23:case 55:case 534:width=4;break;
        case 87:case 119:width=1;break;
        case 279:case 311:case 343:case 375:case 790:width=2;break;
        case 151:case 183:case 662:width=4;write=true;break;
        case 215:case 247:width=1;write=true;break;
        case 407:case 439:case 918:width=2;write=true;break;
        default:break;
        }
        addr=(ra?c.gpr[ra]:0u)+c.gpr[rb];
    }else need(op<48u); // no floating/paired-single memory operations in this scope
    if(width)mapped_word(c,addr,width,write);
}
static bool taken(CPUContext& c,uint32_t w){
    const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
    return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));
}
static void continuation(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.msr==MSR&&c.srr0==0x80030000u&&c.srr1==0x8032u&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx);
    if(pending_reg<32){need(c.gpr[pending_reg]==expected_word);pending_reg=32;}
    if(in_time&&leaf_active){
        auto& leaf=leaves[cursor];
        if(leaf.stage()==3){
            need(leaf.returned(c,pc));leaf_active=false;++cursor;
        }else{
            need(leaf.before(c,pc,w));
            const unsigned xo=(w>>1)&1023u,spr=((w>>11)&31u)*32u+((w>>16)&31u);
            if(cursor==1&&w>>26==31u&&(xo==371u||xo==339u)&&(spr==268u||spr==269u)){
                const auto sample=c.read_timebase();++time_reads;
                if(spr==269u&&!first_upper_delta){need(c.inst_count>initial_tick);first_upper_delta=c.inst_count-initial_tick;}
                pending_reg=(w>>21)&31u;expected_word=uint32_t(spr==269u?sample>>32:sample);
                if(spr==268u)tb_value=sample;
            }
            return;
        }
    }
    if(in_time&&time_done){
        need(pc==TimeResume&&c.pc==pc&&c.lr==pc&&cursor==3&&time_visits==25u&&time_reads>=3u&&polls>=1u&&entries==7u);
        if(corrupt)c.gpr[14]^=1u;
        bool abi=c.gpr[1]==time_gp[1]&&c.gpr[2]==time_gp[2]&&c.gpr[13]==time_gp[13]&&(pack(c)&0x00fff000u)==time_cr;
        for(unsigned i=14;i<32;++i)abi=abi&&c.gpr[i]==time_gp[i];
        if(corrupt){need(!abi);std::cout<<"V802_CALLBACK_REFUSAL abi=1"<<std::endl;std::_Exit(126);}
        need(abi&&offset_reads==2u&&((uint64_t(c.gpr[3])<<32)|c.gpr[4])==tb_value+offset);
        std::cout<<"V811_OWNER_TIME_OFFSET verified=1 nonzero="<<unsigned(offset!=0)<<" wrap="<<unsigned(tb_value+offset<tb_value)<<" retry="<<unsigned(time_reads>3u)<<std::endl;
        need(first_upper_delta>0&&first_upper_delta<=160u);
        std::cout<<"V814_TIMEBASE_GEOMETRY first_upper_delta="<<first_upper_delta<<std::endl;
        if(rollover){need(initial_tick+first_upper_delta==0xffffffffull&&time_reads>=6u&&polls>=2u&&reusable.polls()==polls);
            std::cout<<"V814_TIMEBASE_RETRY verified=1 original_retry=1 original_time_return=1 offset=1 fallback=0"<<std::endl;}
        std::cout<<"V802_OWNER_CALLBACK_TIME original_prologue=1 original_time_return=1 leaves=3 timebase=1 callback_return=0 fallback=0 continuous_boot=0"<<std::endl;std::_Exit(0);
    }
    need(pc==next);
    memory_guard(c,w);
    const unsigned op=w>>26,xo=(w>>1)&1023u;
    next=pc+4u;
    if(in_time){
        need(span(pc,T,system_words.size())&&++time_visits<=25u);
        if(cursor<3&&pc==leaf_sites[cursor]){
            need(w==leaf_branches[cursor]&&leaves[cursor].start(c,pc,w));
            leaf_active=true;return;
        }
        if(w==0x4e800020u){need(cursor==3&&c.lr==TimeResume);time_done=true;next=TimeResume;return;}
        need(op!=16u&&op!=18u);
    }else{
        need(pc>=Resume&&pc<=TimeCall);
        if(pc==TimeCall){
            need(op==18u&&(w&3u)==1u&&pc+(((w&0x03fffffcu)^0x02000000u)-0x02000000u)==T);
            time_gp=c.gpr;time_cr=pack(c)&0x00fff000u;in_time=true;next=T;return;
        }
        if(op==16u||op==18u){
            need(!(w&3u));
            const uint32_t bits=op==16u?0xfffcu:0x03fffffcu,sign=op==16u?0x8000u:0x02000000u;
            const uint32_t dst=pc+(((w&bits)^sign)-sign);
            need(dst>pc&&dst<=TimeCall);
            if(op==18u||taken(c,w))next=dst;
        }
    }
    need(op!=17u&&!(op==19u&&(xo==16u||xo==50u||xo==528u))&&!(op==31u&&xo==146u));
}
namespace rfi_test{
void before(CPUContext& c,uint32_t pc,uint32_t w){
    need(c.inst_count==++tick);
    need(c.mmu.read32(pc)==w);
    ++visits;need(visits<=160);
    if(after_save){
        if(pc==TimeResume&&corrupt){
            if(corrupt_kind==1)c.gpr[14]^=1u;
            if(corrupt_kind==2)c.gpr[4]^=1u;
            if(corrupt_kind==3)c.mmu.write32(Offset+4u,c.mmu.read32(Offset+4u)^1u);
            need(!reusable.before(c,pc,w,true)&&reusable.failure()==5);
            if(corrupt_kind==1)std::cout<<"V802_CALLBACK_REFUSAL abi=1"<<std::endl;
            else std::cout<<"V811_OFFSET_REFUSAL kind="<<corrupt_kind<<std::endl;
            std::_Exit(126);
        }
        need(reusable.before(c,pc,w,true));
        if(pc==TimeResume){need(reusable.stage()==5&&reusable.time_visits()==25&&reusable.cursor()==3&&reusable.timebase()==tb_value&&reusable.system_offset()==offset);std::cout<<"V810_OWNER_TIME_WITNESS verified=1 leaves=3 abi=1 timebase=1 callback_return=0"<<std::endl;}
        continuation(c,pc,w);return;
    }
    need(pc==next);
    state(c);
    if(pc==Resume){
        need(entries==3&&outer==1&&writes==8&&visits==(SaveCall-C)/4u+10u);
        after_save=true;need(reusable.start(c,pc,w,true,true)&&reusable.before(c,pc,w,true));continuation(c,pc,w);return;
    }
    reference(pc,w);
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    constexpr std::array<uint32_t,7> order{H,C,S,T,D,U,R};
    need(c.pc==pc&&entries<order.size()&&pc==order[entries]);
    // The pinned dispatcher increments inst_count once before the first
    // function entry. Subsequent direct calls do not re-enter the dispatcher.
    if(entries==0){need(outer==1&&c.inst_count==tick+1u);++tick;}
    else need(c.inst_count==tick);
    if(entries>=3)need(reusable.entry(c,pc,true));
    if(entries==3)need(in_time&&c.lr==TimeResume);
    if(entries>=4)need(leaf_active&&cursor<3&&leaves[cursor].entry(pc,c));
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(leaf_active){need(cursor==1&&leaves[cursor].poll(c)&&reusable.poll(c,true));++polls;return false;}
    need(!outer&&!visits&&c.pc==H&&c.inst_count==tick);++outer;return false;
}
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
    need(argc==3||argc==4);const std::string mode=argv[1];need(mode=="valid"||mode=="corrupt"||mode=="result"||mode=="offset"||mode=="rollover");
    rollover=mode=="rollover";need(argc==(rollover?4:3));
    corrupt=mode!="valid"&&!rollover;corrupt_kind=mode=="corrupt"?1u:mode=="result"?2u:mode=="offset"?3u:0u;
    unsigned trial=unsigned(std::stoul(argv[2]));need(trial<8);
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(H,caller_words);put(C,prefix_words);put(S,save_words);
    put(T,system_words);put(D,disable_words);put(U,time_words);put(R,restore_words);
    constexpr std::array<uint64_t,8> offsets{0,1,0xffffffffull,0x12345678ffffffffull,UINT64_MAX,0xffffffff00000000ull,0x8000000000000000ull,0x1234ull};
    offset=offsets[trial];c.mmu.write32(Offset,uint32_t(offset>>32));c.mmu.write32(Offset+4u,uint32_t(offset));
    if(trial>=4)tick=0xffffffffull-(35u+trial*2u);
    if(rollover){need(trial==0);tick=std::stoull(argv[3],nullptr,0);need(tick>=0xffffffffull-160u&&tick<0xffffffffull);}
    initial_tick=tick;
    for(unsigned i=0;i<stack.size();++i){stack[i]=0xdeadbeefu^(trial*0x9e3779b9u+i);c.mmu.write32(Low+4*i,stack[i]);}
    for(unsigned i=0;i<32;++i)c.gpr[i]=(i+1u)*0x1234567u^(trial*0x9e3779b9u);
    c.gpr[1]=Stack;c.gpr[2]=0x80025000u;c.gpr[13]=0x8070e8e0u;c.gpr[3]=trial%4;c.gpr[4]=trial&1u;c.gpr[5]=0x80030000u;
    gp=c.gpr;
    for(unsigned i=0;i<8;++i){c.cr[i].lt=bool((i+trial)&1);c.cr[i].gt=bool((i+trial)&2);c.cr[i].eq=bool((i+trial)&4);c.cr[i].so=bool((i+trial)&8);}
    cr=pack(c);ctr=c.ctr=0x12345678u+trial;xer=c.xer=0x80000000u|trial;
    c.pc=H;lr=c.lr=0x80007000u;c.msr=MSR;c.srr0=0x80030000u;c.srr1=0x8032u;c.inst_count=tick;
    c.is_running=true;c.in_callback=false;c.dispatch_saved_ctx=0;
    run_game(c);fail(8);
}catch(...){fail(8);}
