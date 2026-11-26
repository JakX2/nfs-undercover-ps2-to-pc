#include "runtime/cpu_context.h"
#include "wii_second_si_dispatch_v944.h"
#include "wii_second_completion_ack_v950.h"
#include "wii_bounded_ack_call_route_v956.h"
#include "wii_si_type_scheduler_v514.h"
#include "owner_second_dispatch.h"
#include "rfi_test_v708.h"
#include <algorithm>
#include <array>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <vector>
#include <memory>
#include <source_location>
#include <string>
using namespace undercover::wii;
using nwii::runtime::CPUContext;
constexpr uint32_t Context=SiDispatchWitness::Thread,Resume=0x80004000u,Other=0x100u,Mask=0xf8u,Sda=0x8070e8e0u;
static SecondSiDispatchWitness witness(DispatchExpected);
static ExternalReturnWitness captured;
static SecondCompletionAck ack;
static std::atomic<uint32_t> bank_mask{Mask};
static BoundedAckCallRoute call_route;
static const auto ack_spans=[] {
    std::vector<AckCallSpan> result{
    {Handler,Handler+4u*uint32_t(handler_words.size())},
    {Save,Save+4u*uint32_t(save_words.size()),1},
    {Completion,Completion+4u*uint32_t(completion_words.size())},
    {Nested,Nested+4u*uint32_t(nested_words.size())},
    {Disable,Disable+4u*uint32_t(disable_words.size())},
    {Time,Time+4u*uint32_t(time_words.size())},
    {Restore,Restore+4u*uint32_t(restore_words.size())},
    {Transfer,Transfer+4u*uint32_t(transfer_words.size())},
    {TransferRestore,TransferRestore+4u*uint32_t(transfer_restore_words.size()),0,26}
    };
    if(TransferSave!=Save)result.push_back({TransferSave,TransferSave+4u*uint32_t(transfer_save_words.size()),1});
    return result;
}();
static constexpr auto ack_edges=[]{
    std::array<AckCallEdge,AckEdges.size()> result{};
    for(unsigned i=0;i<result.size();++i)result[i]={AckEdges[i][0],AckEdges[i][1]};
    return result;
}();
static unsigned ack_visits=0,ack_entries=0;
static std::atomic<uint32_t> cause{Other};
static SiController* ctl=nullptr;
static SiTypeScheduler* scheduler=nullptr;
static PostAckTransferDevice third;
static bool transfer_route=false,transfer_idle=false,seeded_route=false,argument_probe=false;
static unsigned seed_kind=0;
static bool suffix_route=false,alarm_route=false,shared_route=false,shared_seen=false,shared_continue=false;
static unsigned shared_tick=0,shared_entries=0,shared_returns=0,shared_msr=0;
static bool callback_route=false;
static CallbackPrefixWitness<callback_prefix.size(),callback_save.size()> callback_witness(CallbackRoot,CallbackSave,callback_prefix,callback_save);
static AlarmCancelReturnWitness alarm_witness(v786::expected);
static HandlerSuffixGuard suffix_guard;
static unsigned suffix_reg=32,suffix_tick=0;
static bool suffix_write=false;
static std::array<uint32_t,32> handler_gp{};
static uint32_t handler_lr=0;
static unsigned transfer_channel=0,transfer_tick=0,transfer_entries=0,transfer_returns=0;
static std::array<uint32_t,32> transfer_args{};
constexpr uint32_t TransferData=0x80619a60u;
static std::array<uint32_t,32> held_buffer{};
static uint32_t held_control=0,held_status=0;
static unsigned trial=0,visits=0,entries=0,polls=0,reads=0;
static uint64_t last=0;
static bool bad_frame=false,bad_pi=false,postack=false,time_route=false,post_seen=false,frontier_route=false,time_seen=false;
static unsigned time_entries=0,time_returns=0,time_msr=0,time_tick=0,time_return_visit=0;
static unsigned ack_returns=0,ack_boundary_visits=0;
static bool held(){
    if(!ctl||ctl->pending()||ctl->issued_tokens()!=2u||cause.load()!=(Other|8u)||
       ctl->read(SiController::Control)!=held_control||ctl->read(SiController::Status)!=held_status)return false;
    for(unsigned i=0;i<32;++i)if(ctl->read(SiController::Buffer+4*i)!=held_buffer[i])return false;
    return true;
}
[[noreturn]]static void fail(unsigned kind,unsigned line=0){
    std::cout<<std::dec<<"V955_ACK_FAULT kind="<<kind<<" line="<<line<<" trial="<<trial<<" visits="<<visits
        <<" ack_stage="<<ack.stage()<<" ack_reason="<<ack.failure()<<" ack_visits="<<ack_visits<<" ack_entries="<<ack_entries<<" stage="<<witness.stage()<<" reason="<<witness.failure()<<" entries="<<entries<<" polls="<<polls<<" reads="<<reads<<std::endl;
    std::_Exit(126);
}
static void need(bool ok,const std::source_location loc=std::source_location::current()){if(!ok)fail(1,loc.line());}
// The runner authenticates this same DOL against the owner hash before
// invoking the fixture. Copy only initialized data sections, not code.
static void load_private_data(CPUContext& c,const char* path){
    std::ifstream f(path,std::ios::binary|std::ios::ate);need(bool(f));
    const auto n=f.tellg();need(n>=256&&n<=32*1024*1024);
    std::vector<uint8_t> raw(static_cast<size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(raw.data()),n);need(bool(f));
    auto be=[&](unsigned off){return (uint32_t(raw[off])<<24)|(uint32_t(raw[off+1])<<16)|(uint32_t(raw[off+2])<<8)|raw[off+3];};
    std::vector<std::pair<uint32_t,uint32_t>> ranges;
    for(unsigned i=7;i<18;++i){
        const uint32_t off=be(4*i),base=be(0x48+4*i),size=be(0x90+4*i);
        if(!size)continue;
        need(off>=256u&&uint64_t(off)+size<=raw.size()&&base>=0x80000000u&&uint64_t(base)+size<=0x81800000u);
        for(auto [a,b]:ranges)need(base>=b||uint64_t(base)+size<=a);
        auto* p=c.mmu.get_ptr(base);need(p&&c.mmu.get_ptr(base+size-1u)==p+size-1u);
        std::copy_n(raw.data()+off,size,p);ranges.emplace_back(base,base+size);
    }
    need(!ranges.empty());
}
static void suffix_before(CPUContext& c,uint32_t owner,uint32_t pc,uint32_t w){
    need(owner==Handler&&third.stage()==2u&&call_route.depth()==0u&&!(c.msr&0x8000u)&&third.held_now());
    if(suffix_reg<32u){
        const auto value=third.suffix_status_value();need(value&&c.gpr[suffix_reg]==*value);
        suffix_reg=32u;
    }
    if(suffix_write){need(third.suffix_status_writes()==1u);suffix_write=false;}
    const auto row=std::find_if(TransferSuffix.begin(),TransferSuffix.end(),[pc](const auto& v){return v.pc==pc;});
    need(row!=TransferSuffix.end());
    if(std::find(TransferOtherStops.begin(),TransferOtherStops.end(),pc)!=TransferOtherStops.end()){
        // Unsupported control forms remain refusal boundaries, not executed
        // instructions. The private geometry supplied the exact location.
        need(w==0x4e800020u&&row->word==w&&suffix_guard.before(c,pc,w,0,0)&&third.held_now()&&third.token()==3u&&
             !ctl->pending()&&cause==(Other|SiController::PI_SI));
        std::cout<<std::dec<<"V982_TRANSFER_OTHER_STOP seed="<<seed_kind<<" profile="<<trial<<" visits="
                 <<ack_visits-suffix_tick<<" token_held=1 saved_fields=38 boundary_executed=0"<<std::endl;
        std::_Exit(0);
    }
    const auto a=PostAckTransferDevice::word_access(c,w);
    const auto off=PostAckTransferDevice::offset(a.address);
    const bool rd=off&&*off==SiController::Status&&a.kind==PostAckTransferDevice::Access::Read;
    const bool wr=off&&*off==SiController::Status&&a.kind==PostAckTransferDevice::Access::Write;
    need(!off||rd||wr);
    need(suffix_guard.before(c,pc,w,row->ordinal,row->kind,rd,wr));
    if(row->kind||w==0x4e800020u){
        const bool returned=!row->kind;
        if(returned){
            need(std::find(Guard.begin(),Guard.end(),pc)==Guard.end()&&c.lr==handler_lr);
            for(unsigned i:{1u,2u,13u})need(c.gpr[i]==handler_gp[i]);
            for(unsigned i=14;i<32;++i)need(c.gpr[i]==handler_gp[i]);
        }
        need(third.held_now()&&third.token()==3u&&ctl->issued_tokens()==3u&&!ctl->pending()&&cause==(Other|SiController::PI_SI));
        if(alarm_route&&row->kind==1u&&row->ordinal==5u){
            need(std::find(Guard.begin(),Guard.end(),pc)==Guard.end()&&alarm_witness.start(c,pc,w,third.held_now()));
            std::cout<<std::dec<<"V985_ALARM_ENTRY lane="<<alarm_witness.lane()<<" timer="<<alarm_witness.timer_required()<<std::endl;
            return;
        }
        std::cout<<std::dec<<"V980_TRANSFER_SUFFIX seed="<<seed_kind<<" profile="<<trial<<" ordinal="<<row->ordinal
            <<" kind="<<row->kind<<" handler_blr="<<returned<<" callback_candidate="<<(row->kind==2u&&c.ctr==0x805327f8u)
            <<" visits="<<ack_visits-suffix_tick<<" status_reads="<<third.suffix_status_reads()<<" status_writes="<<third.suffix_status_writes()
            <<" token_held=1 saved_fields=38 boundary_executed=0"<<std::endl;
        std::_Exit(0);
    }
    if(rd){need(third.arm_suffix_status_read(c.inst_count,a.address));suffix_reg=(w>>21)&31u;}
    if(wr){need(a.store&&third.arm_suffix_status_write(c.inst_count,a.address,*a.store));suffix_write=true;}
}
namespace rfi_test {
void before_owned(CPUContext& c,uint32_t owner,uint32_t pc,uint32_t w){
    if(ack.stage()){
        need(captured.saved_integer(c,Context).ok()&&++ack_visits<=8192u);
        if(callback_witness.stage()){
            need(ack.stage()==4u&&ack.before(c,pc,w,true)&&ack.postack_held()&&cause==Other&&
                 (owner==CallbackRoot||owner==CallbackSave)&&callback_witness.before(c,pc,w,true));
            if(callback_witness.stage()==6u){
                std::cout<<std::dec<<"V994_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes="<<callback_witness.writes()
                    <<" visits="<<callback_witness.visits()<<" token_preserved=1 saved_fields=38 continuation_executed=0"<<std::endl;
                std::_Exit(0);
            }
            return;
        }
        if(third.stage()==2u){
            need(suffix_route&&ack.stage()==5u);
            scheduler->advance(c.inst_count);need(third.after_return_at(c.inst_count));
            if(alarm_witness.stage()){
                need(alarm_route&&third.held_now()&&std::find(Guard.begin(),Guard.end(),pc)==Guard.end());
                if(alarm_witness.stage()==3u){
                    need(owner==Handler&&alarm_witness.returned(c,pc,w,third.held_now())&&third.token()==3u&&cause==(Other|SiController::PI_SI));
                    std::cout<<std::dec<<"V985_ALARM_RETURN original_return=1 queue=1 lane="<<alarm_witness.lane()<<" timer="<<alarm_witness.timer_required()
                        <<" calls="<<alarm_witness.calls()<<" visits="<<alarm_witness.total()<<" token_held=1 saved_fields=38 handler_instruction_executed=0"<<std::endl;
                    std::_Exit(0);
                }
                need(alarm_witness.native_before(c,pc,w,third.held_now()));return;
            }
            suffix_before(c,owner,pc,w);return;
        }
        if(third.stage()){
            need(ack.stage()==5u&&third.stage()==1u&&std::find(Guard.begin(),Guard.end(),pc)==Guard.end()&&c.mmu.read32(pc)==w);
            scheduler->advance(c.inst_count);
            const auto a=PostAckTransferDevice::word_access(c,w);
            const auto off=PostAckTransferDevice::offset(a.address);
            if(a.kind!=PostAckTransferDevice::Access::None&&!off){
                const uint32_t p=a.address&0x3fffffffu;
                auto overlaps=[p](uint32_t base){return p<base+0x100u&&uint64_t(p)+4u>base;};
                need(!overlaps(0x0d006400u)&&!overlaps(0x0d806400u));
            }
            need(third.before(c.inst_count,off?a.kind:PostAckTransferDevice::Access::None,off?a.address:0,off?a.store:std::nullopt));
            need(call_route.before(c,pc,w,owner));
            if(pc==TransferCall+4u){
                need(owner==Handler&&call_route.depth()==0u&&call_route.entries()-transfer_entries>=4u&&
                     call_route.entries()-transfer_entries==call_route.returns()-transfer_returns&&
                     third.finish(c.inst_count,c.gpr[3])&&third.held_now()&&bank_mask==Mask);
                if(transfer_idle){
                    need(third.token()==3u&&ctl->issued_tokens()==3u&&third.follow_stage()>=2u&&
                         c.mmu.read32(TransferData)==transfer_channel&&c.mmu.read32(TransferData+8u)==transfer_args[7]&&
                         c.mmu.read32(TransferData+12u)==transfer_args[6]&&c.mmu.read32(TransferData+16u)==transfer_args[8]);
                }else need(ctl->issued_tokens()==2u&&!third.reads()&&!third.writes()&&cause==Other);
                std::cout<<std::dec<<"V972_TRANSFER_RETURN original_transfer=1 idle="<<transfer_idle<<" token="<<ctl->issued_tokens()
                         <<" pending="<<third.pending()<<" visits="<<ack_visits-transfer_tick<<" reads="<<third.reads()<<" writes="<<third.writes()
                         <<" saved_fields=38 handler_instruction_executed=0"<<std::endl;
                if(!suffix_route)std::_Exit(0);
                need(third.token()==3u&&third.follow_stage()==3u);
                need(suffix_guard.start(c,TransferSuffix,pc,256u));
                suffix_tick=ack_visits;suffix_before(c,owner,pc,w);
            }
            return;
        }
        if(pc==CallbackCall){
            need(owner==Handler&&shared_seen&&post_seen&&ack.stage()==4u&&call_route.depth()==0u&&call_route.can_poll()&&
                 ack.before(c,pc,w,true)&&ack.postack_held()&&c.ctr==CallbackRoot&&
                 classify_callback_identity(c,pc,w,6,2,CallbackRoot,callback_full,callback_sites)==2u);
            if(callback_route){need(callback_witness.start_dispatch(c,pc,w,true,true));return;}
            need(argument_probe&&shared_continue);
            std::cout<<std::dec<<"V992_SUCCESS_FRONTIER seed="<<seed_kind<<" profile="<<trial
                <<" lane=1 ordinal=6 kind=2 time_return="<<time_seen<<" callback_candidate=1 visits="<<ack_visits-ack_boundary_visits
                <<" token_preserved=1 saved_fields=38 call_executed=0"<<std::endl;
            std::_Exit(0);
        }
        if(std::find(Guard.begin(),Guard.end(),pc)!=Guard.end()){
            if(argument_probe&&(ack.stage()==1u||ack.stage()==4u)&&w==0x4e800020u){
                for(const auto& row:GuardCensus)if(pc==row[0]){
                    need(ack.before(c,pc,w,true)&&ack.poll(c.inst_count)&&bank_mask==Mask&&ctl->issued_tokens()==2u);
                    if(shared_continue){
                        need(shared_seen&&post_seen&&ack.stage()==4u&&ack.postack_held());
                        std::cout<<std::dec<<"V992_SUCCESS_FRONTIER seed="<<seed_kind<<" profile="<<trial
                            <<" lane="<<row[1]<<" ordinal="<<row[2]<<" kind="<<row[3]<<" time_return="<<time_seen
                            <<" callback_candidate="<<(row[3]==2u&&c.ctr==0x805327f8u)
                            <<" visits="<<ack_visits-ack_boundary_visits<<" token_preserved=1 saved_fields=38 call_executed=0"<<std::endl;
                    }
                    std::cout<<std::dec<<"V976_GUARD_PROFILE seed="<<seed_kind<<" profile="<<trial<<" lane="<<row[1]
                             <<" ordinal="<<row[2]<<" category="<<row[3]<<" stage="<<ack.stage()<<" depth="<<call_route.depth()
                             <<" time_return="<<time_seen<<" visits="<<ack_visits<<" original_guard_executed=0"<<std::endl;
                    std::_Exit(0);
                }
            }
            // A synthetic refusal guard is never executed. Its original
            // call identity was authenticated privately before translation.
            if(frontier_route&&time_seen&&ack.stage()==4u&&call_route.depth()==0u&&w==0x4e800020u){
                for(const auto& f:HandlerFrontier)if(pc==f[0]){
                    need(ack.before(c,pc,w,true)&&ack.postack_held()&&cause==Other&&bank_mask==Mask&&ack_visits>time_return_visit);
                    std::cout<<std::dec<<"V968_HANDLER_FRONTIER ordinal="<<f[1]<<" kind="<<f[2]
                        <<" visits="<<ack_visits-time_return_visit<<" token_preserved=1 saved_fields=38 call_executed=0"<<std::endl;
                    std::_Exit(0);
                }
            }
            fail(11);
        }
        need(ack.before(c,pc,w,true));
        if(ack.stage()==3u){
            need(call_route.before(c,pc,w,owner));
            need(call_route.returns()>=1u&&ack.token()==2u&&ack.reads()>0u&&ack.writes()>0u&&cause==Other&&bank_mask==Mask&&ack_entries>=2u);
            std::cout<<"V955_ACK_TRIAL verified=1 original_w1c=1 next_label=1 saved_fields=38 token=2"<<std::endl;
            if(!postack)std::_Exit(0);
            ack_returns=call_route.returns();ack_boundary_visits=ack_visits;
            need(ack.resume_after_ack(c,pc,w));return;
        }
        if(pc==TransferCall&&frontier_route&&!transfer_route){
            need(time_seen&&ack.stage()==4u&&ack.postack_held()&&owner==Handler&&call_route.depth()==0u);
            std::cout<<"V968_HANDLER_FRONTIER ordinal=4 kind=1 visits="<<ack_visits-time_return_visit
                     <<" token_preserved=1 saved_fields=38 call_executed=0"<<std::endl;
            std::_Exit(0);
        }
        need(call_route.before(c,pc,w,owner));
        if(pc==CompletionTimeCall){
            need(shared_route&&!shared_tick&&owner==Completion&&call_route.depth()==2u&&ack.postack_held());
            shared_tick=ack_visits;shared_entries=call_route.entries();shared_returns=call_route.returns();shared_msr=call_route.msr_writes();
        }
        if(shared_tick&&pc==CompletionTimeCall+4u){
            need(!shared_seen&&owner==Completion&&call_route.depth()==1u&&call_route.entries()-shared_entries==4u&&
                 call_route.returns()-shared_returns==4u&&call_route.msr_writes()-shared_msr==2u&&ack.postack_held());
            shared_seen=true;
            std::cout<<std::dec<<"V988_SHARED_TIME_RETURN original_time=1 leaves=3 unchanged_msr=2 visits="<<ack_visits-shared_tick
                <<" token_preserved=1 saved_fields=38"<<std::endl;
        }
        if(transfer_route&&pc==TransferCall){
            need(time_seen&&ack.stage()==4u&&ack.postack_held()&&owner==Handler&&call_route.depth()==1u&&c.gpr[3]<4u);
            auto mapped=[&](uint32_t a,unsigned n){return a>=0x80000000u&&uint64_t(a)+n<=0x81800000u&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);};
            const bool out_mapped=mapped(c.gpr[4],1),in_mapped=mapped(c.gpr[6],3),callback=mapped(c.gpr[8],4)&&!(c.gpr[8]&3u);
            const bool command_zero=out_mapped&&c.mmu.read8(c.gpr[4])==0u;
            const bool type=c.gpr[5]==1u&&c.gpr[7]==3u&&out_mapped&&in_mapped&&callback&&command_zero;
            std::cout<<std::dec<<"V973_TRANSFER_ARGS seeded="<<seeded_route<<" profile="<<trial
                <<" out_one="<<(c.gpr[5]==1u)<<" in_three="<<(c.gpr[7]==3u)<<" out_mapped="<<out_mapped
                <<" in_mapped="<<in_mapped<<" callback="<<callback<<" command_zero="<<command_zero
                <<" idle="<<(c.mmu.read32(TransferData)==0xffffffffu)<<" type="<<type<<std::endl;
            if(argument_probe){
                if(shared_continue){
                    need(shared_seen&&post_seen&&time_seen&&ack.postack_held());
                    std::cout<<std::dec<<"V992_SUCCESS_FRONTIER seed="<<seed_kind<<" profile="<<trial
                        <<" lane=1 ordinal=4 kind=1 time_return=1 callback_candidate=0 visits="<<ack_visits-ack_boundary_visits
                        <<" token_preserved=1 saved_fields=38 call_executed=0"<<std::endl;
                }
                std::cout<<"V976_ARG_PROFILE seed="<<seed_kind<<" profile="<<trial<<" admissible="<<type<<" original_transfer_executed=0"<<std::endl;
                std::_Exit(0);
            }
            need(type);
            transfer_channel=c.gpr[3];transfer_args=c.gpr;
            transfer_idle=c.mmu.read32(TransferData)==0xffffffffu;
            transfer_entries=call_route.entries();transfer_returns=call_route.returns();transfer_tick=ack_visits;
            scheduler->advance(c.inst_count);
            const auto cfg=scheduler->configuration(*ctl,transfer_channel,c.inst_count);
            need(cfg&&ack.handoff_follow_on(third,*ctl,cause,bank_mask,c.inst_count,transfer_channel,transfer_idle,cfg->response,cfg->latency));
            return;
        }
        if(ack.stage()==4u&&!post_seen&&pc>=Handler&&pc<Handler+4u*handler_words.size()&&call_route.depth()==0u){
            need(call_route.returns()>ack_returns&&ack_visits>ack_boundary_visits&&ack.token()==2u&&cause==Other&&bank_mask==Mask);
            std::cout<<std::dec<<"V962_POST_ACK_RETURN original_helper_return=1 saved_fields=38 token_preserved=1 visits="<<ack_visits-ack_boundary_visits<<" handler_instruction_executed=0"<<std::endl;
            if(shared_route){
                need(shared_seen&&ack.postack_held());
                std::cout<<std::dec<<"V988_SUCCESS_HELPER_RETURN seed="<<seed_kind<<" profile="<<trial<<" original_helper_return=1 shared_time=1 visits="
                    <<ack_visits-ack_boundary_visits<<" token_preserved=1 saved_fields=38 handler_instruction_executed=0"<<std::endl;
                if(!shared_continue)std::_Exit(0);
            }
            if(!time_route)std::_Exit(0);
            post_seen=true;
        }
        if(time_route&&post_seen&&pc==TimeCall){
            need(!time_tick&&call_route.depth()==1u);
            time_entries=call_route.entries();time_returns=call_route.returns();time_msr=call_route.msr_writes();time_tick=ack_visits;
        }
        if(time_route&&!time_seen&&time_tick&&pc==TimeCall+4u){
            need(call_route.depth()==0u&&call_route.entries()-time_entries==4u&&call_route.returns()-time_returns==4u&&
                 call_route.msr_writes()-time_msr==2u&&ack.postack_held()&&cause==Other&&bank_mask==Mask);
            std::cout<<std::dec<<"V966_TIME_RETURN original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 visits="<<ack_visits-time_tick<<" handler_instruction_executed=0"<<std::endl;
            if(!frontier_route)std::_Exit(0);
            time_seen=true;time_return_visit=ack_visits;
        }
        return;
    }
    need(held()&&!(c.msr&0x8000u)&&c.mmu.read32(pc)==w&&
         std::find(Guard.begin(),Guard.end(),pc)==Guard.end());
    need(c.inst_count-last==1u&&++visits<=2048u);
    last=c.inst_count;
}
}
namespace nwii::runtime{
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(callback_witness.stage()){
        need(captured.saved_integer(c,Context).ok());
        if(callback_witness.stage()==1u)need(ack.accept_dispatch_tick(c));
        need(ack.postack_held()&&callback_witness.entry(c,pc,true));return;
    }
    if(alarm_witness.stage()){need(captured.saved_integer(c,Context).ok()&&alarm_witness.entry(c,pc,third.held_now()));return;}
    if(ack.stage()){
        need(call_route.entry(c,pc)&&(third.stage()?third.held_now():ack.poll(c.inst_count)));
        ++ack_entries;return;
    }
    if(!entries){need(pc==Dispatcher&&witness.begin(c,captured,cause.load(),Mask,held()));last=c.inst_count;++entries;return;}
    if(pc==Handler&&bad_frame)c.mmu.write32(Context+4u*31,c.mmu.read32(Context+4u*31)^1u);
    const bool ok=witness.observe(c,pc,cause.load(),Mask,held());
    if(bad_frame&&pc==Handler){need(!ok&&witness.failure()==3u);std::cout<<"V946_FRAME_REFUSAL saved_gpr=1"<<std::endl;std::_Exit(126);}
    if(bad_pi&&!ok){need(witness.failure()==3u);std::cout<<"V946_PI_REFUSAL wrong_value=1"<<std::endl;std::_Exit(126);}
    need(ok);
    if(pc==Handler){
        need(witness.stage()==6u&&entries==5u&&reads>=2u&&captured.saved_integer(c,Context).ok());
        handler_gp=c.gpr;handler_lr=c.lr;
        need(call_route.begin(c,ack_spans,ack_edges,AckMsr));
        need(ack.arm(*ctl,cause,bank_mask,c.inst_count,ctl->issued_tokens(),held()));
        ++entries;return;
    }
    ++entries;
}
bool process_pending_callbacks(CPUContext& c){
    if(callback_witness.stage()){need(captured.saved_integer(c,Context).ok()&&ack.postack_held()&&callback_witness.dispatch_poll(c,true));return false;}
    if(alarm_witness.stage()){need(captured.saved_integer(c,Context).ok()&&alarm_witness.poll(c,third.held_now()));return false;}
    if(ack.stage()){need(call_route.can_poll()&&(third.stage()?third.held_now():ack.poll(c.inst_count)));++polls;return false;}
    if(!entries){need(c.pc==Dispatcher&&held());return false;}
    const bool ok=witness.poll(c,cause.load(),Mask,held());
    if(bad_pi&&!ok){need(witness.failure()==2u);std::cout<<"V946_PI_REFUSAL wrong_value=1"<<std::endl;std::_Exit(126);}
    need(ok);
    if(c.inst_count==last+1u)last=c.inst_count;
    else need(c.inst_count==last);
    ++polls;return false;
}
bool handle_syscall(CPUContext&){fail(2);}
void interpret_step(CPUContext&){fail(3);}
void micro_interpret(CPUContext&,uint32_t,uint32_t){fail(4);}
void note_null_call(uint32_t,uint32_t){fail(5);}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){fail(6);}void GX_WGPIPE_Write16(uint16_t){fail(6);}void GX_WGPIPE_Write32(uint32_t){fail(6);}
void GX_WGPIPE_WriteF32(float){fail(6);}void GX_WGPIPE_WriteF64(double){fail(6);}
uint16_t HW_Reg_Read16(uint32_t){fail(7);}
uint32_t HW_Reg_Read32(uint32_t a){
    if(ack.stage()){
        const auto off=PostAckTransferDevice::offset(a);uint32_t v=0;
        need(off&&(third.stage()?third.read(*ctl,*off,v):ack.read(*ctl,*off,v)));return v;
    }
    if(a!=0x0c003000u&&a!=0x0c003004u)fail(7);
    const uint32_t v=a==0x0c003000u?cause.load():Mask;
    witness.record(false,a,32,v^(bad_pi&&reads==0?8u:0u),false);++reads;
    return v; // actual bus result, negative control corrupts observer only
}
void HW_Reg_Write16(uint32_t,uint16_t){fail(8);}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    const auto off=PostAckTransferDevice::offset(a);
    need(off&&(third.stage()?third.write(*ctl,*off,v):((ack.stage()==1u||ack.stage()==4u)&&ack.write(*ctl,*off,v))));
}
}
extern "C" void run_game(CPUContext&);
int main(int argc,char** argv)try{
    need(argc==4);trial=unsigned(std::stoul(argv[1]));need(trial<8);
    const std::string mode=argv[2];need(mode=="valid"||mode=="bad-frame"||mode=="bad-pi"||mode=="postack"||mode=="time"||mode=="frontier"||mode=="transfer"||mode=="args"||mode=="seeded-args"||mode=="queue-args"||mode=="active-args"||mode=="queue-transfer"||mode=="active-transfer"||mode=="queue-suffix"||mode=="seeded-suffix"||mode=="queue-alarm"||mode=="seeded-alarm"||mode=="active-success"||mode=="seeded-success"||mode=="active-frontier"||mode=="seeded-frontier"||mode=="active-callback"||mode=="successful-alarm");
    bad_frame=mode=="bad-frame";bad_pi=mode=="bad-pi";
    callback_route=mode=="active-callback";
    shared_continue=mode=="active-frontier"||mode=="seeded-frontier"||callback_route||mode=="successful-alarm";
    shared_route=mode=="active-success"||mode=="seeded-success"||shared_continue;
    alarm_route=mode=="queue-alarm"||mode=="seeded-alarm"||mode=="successful-alarm";
    suffix_route=mode=="queue-suffix"||mode=="seeded-suffix"||alarm_route;
    seed_kind=mode=="seeded-args"||mode=="transfer"||mode=="seeded-suffix"||mode=="seeded-alarm"||mode=="seeded-success"||mode=="seeded-frontier"||mode=="successful-alarm"?3u:mode=="queue-args"||mode=="queue-transfer"||mode=="queue-suffix"||mode=="queue-alarm"?1u:mode=="active-args"||mode=="active-transfer"||mode=="active-success"||mode=="active-frontier"||callback_route?2u:0u;
    seeded_route=seed_kind!=0;argument_probe=mode=="args"||mode=="seeded-args"||mode=="queue-args"||mode=="active-args"||(shared_continue&&!callback_route&&mode!="successful-alarm");
    transfer_route=seeded_route||argument_probe;frontier_route=mode=="frontier"||transfer_route;time_route=mode=="time"||frontier_route;postack=mode=="postack"||time_route;
    auto cpu=std::make_unique<CPUContext>();auto& c=*cpu;
    load_private_data(c,argv[3]);
    auto put=[&](uint32_t a,const auto& ws){for(auto w:ws){c.mmu.write32(a,w);a+=4;}};
    put(Dispatcher,dispatcher_words);put(Scheduler,scheduler_words);put(Time,time_words);put(Disable,disable_words);put(Restore,restore_words);put(Handler,handler_words);put(Save,save_words);put(Completion,completion_words);put(Nested,nested_words);
    put(Transfer,transfer_words);put(TransferSave,transfer_save_words);put(TransferRestore,transfer_restore_words);
    put(Alarm,alarm_words);put(AlarmTimer,alarm_timer_words);
    put(CallbackRoot,callback_full);
    SiController dev(cause);ctl=&dev;
    const std::array<uint8_t,3> response{9,0,0};
    const uint32_t cfg=SiController::TC_MASK|(1u<<16)|(3u<<8)|((trial%4u)<<1);
    dev.write(SiController::Control,cfg|SiController::TSTART);dev.complete(dev.pending()->token,response);
    dev.write(SiController::Control,cfg|SiController::TC_INT);need(cause.load()==Other);
    dev.write(SiController::Control,cfg|SiController::TSTART);
    if(trial&4u)dev.complete(dev.pending()->token,{},SiController::ERR_NOREP);else dev.complete(dev.pending()->token,response);
    held_control=dev.read(SiController::Control);held_status=dev.read(SiController::Status);
    for(unsigned i=0;i<32;++i)held_buffer[i]=dev.read(SiController::Buffer+4*i);
    need(held());
    using Port=SiTypeScheduler::Port;
    const auto port=(trial&4u)?Port::absent():Port::present({9,0,0});
    SiTypeScheduler sched(dev,{port,port,port,port},8);scheduler=&sched;
    c.gpr.fill(0);c.gpr[1]=0x80751cb8u-88u;c.gpr[2]=0x80715ee0u;c.gpr[13]=Sda;
    for(unsigned i=14;i<32;++i)c.gpr[i]=i*0x1234567u+trial;
    c.cr.fill({});c.pc=Resume;c.lr=0x80006000u;c.ctr=17;c.xer=0x80000000u;
    c.msr=0x8032u;c.srr0=c.srr1=0;c.inst_count=100;c.is_running=true;
    need(captured.capture(c,cause.load(),Mask));
    for(unsigned i=0;i<32;++i)c.mmu.write32(Context+4*i,c.gpr[i]);
    c.mmu.write32(Context+128,0);c.mmu.write32(Context+132,c.lr);c.mmu.write32(Context+136,c.ctr);c.mmu.write32(Context+140,c.xer);
    c.mmu.write32(Context+408,Resume);c.mmu.write32(Context+412,c.msr);
    c.mmu.write32(0x800000c0u,Context&0x3fffffffu);c.mmu.write32(0x800000c4u,0xf7fff7f0u);c.mmu.write32(0x800000c8u,0);
    c.mmu.write32(0x800000d4u,Context);c.mmu.write32(0x800000e4u,Context);
    c.mmu.write32(Sda+SchedulerCounterDisp,0u);
    c.mmu.write32(Sda-3408u,0x80003040u);c.mmu.write32(0x80003090u,Handler);
    if(seeded_route){
        // Explicit focused fixture: reconstruct the queued SI type packets
        // from the previously verified V529 cold-discovery guest layout.
        // No changes to guest RAM after native execution has begun.
        constexpr uint32_t Slot=0x806fe340u,TypeData=TransferData+24u,Command=Sda-3144u,Callback=0x805327f8u;
        const unsigned completed=trial%4u,next=(completed+1u)%4u;
        c.mmu.write32(Command,0u);
        if(seed_kind&2u){
            c.mmu.write32(TransferData,completed);
            c.mmu.write32(TransferData+8u,3u);c.mmu.write32(TransferData+12u,TypeData+4u*completed);
            c.mmu.write32(TransferData+16u,Callback);
        }
        for(unsigned ch=0;ch<4;++ch){
            c.mmu.write32(TypeData+4u*ch,128u);
            for(unsigned i=0;i<8;++i)c.mmu.write32(Slot+32u*ch+4u*i,0u);
            c.mmu.write32(Slot+32u*ch,0xffffffffu);
            c.mmu.write32(Slot+160u+8u*ch,0u);c.mmu.write32(Slot+164u+8u*ch,0u);
        }
        if(seed_kind&1u){
            const std::array<uint32_t,8> packet{next,Command,1u,TypeData+4u*next,3u,Callback,0u,0u};
            for(unsigned i=0;i<packet.size();++i)c.mmu.write32(Slot+32u*next+4u*i,packet[i]);
        }
    }
    c.pc=Dispatcher;c.gpr[3]=4;c.gpr[4]=Context;c.msr=0x32u;c.srr0=Resume;c.srr1=0x8032u;c.inst_count=150u;
    run_game(c);fail(9);
}catch(...){fail(10);}
