#include "runtime/cpu_context.h"
#include "functions.h"
#include "v624_private_ipc_expectations.h"
#include "v626_private_words.h"
#include "wii_post_ack_sleep_join_v1252.h"
#include "v1252_private_sleep.h"
#include "v1256_private_scheduler.h"
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
#include "wii_scheduler_irq_entry_v1259.h"
#include "v1259_private_vector.h"
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
#include "wii_second_vector_v939.h"
#include "v1260_private_vector.h"
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
#include "v1261_private_dispatch.h"
#include "wii_initialized_dol_data_v1264.h"
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
#include "v1266_private_ack.h"
#include "wii_joined_ipc_ack_v1266.h"
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
#include "v1270_private_epilogue.h"
#include "wii_scheduler_reply_irq_v1268.h"
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
#include "wii_joined_ipc_reply_entry_v1273.h"
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
#include "v1281_private_reply.h"
#endif
#include "v639_private_open_expectations.h"
#include "v629_private_stm_expectations.h"
#include "v1243_private_stm_data.h"
#include "wii_second_completion_ack_v950.h"
#include <algorithm>
#include <iostream>
#include <string_view>
#include <memory>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=IpcClientWitness;using B=NativeIosBinding;using H=HollywoodIrq;using M=IpcMailbox;
namespace nw=nwii::runtime;
static std::atomic<uint32_t> cause{0},mask{0xf0};
static PostAckIpcJoin* witness=nullptr;
static PostAckStmJoin* stm_witness=nullptr;
static PostAckOpenJoin* open_witness=nullptr;
static unsigned stm_entries=0,open_entries=0,open_vectors=0,open_returns=0,open_polls=0;
struct RequestReached{};struct SubmitStop{};struct SleepStop{};
static PostAckSleepJoin* sleep_join=nullptr;
static unsigned sleep_count=0;
struct SchedulerStop{};
static PostAckSchedulerJoin* sched_join=nullptr;
static unsigned scheduler_count=0;
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
static unsigned irq_count=0;
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
static ExternalReturnWitness irq_capture;
static constexpr SecondVectorExpectation ipc_vector_expected{v1260::trampoline,v1260::dispatcher,
    PostAckSchedulerJoin::Idle,v1260::dispatcher_word,v1260::vector_words,v1260::trampoline_words};
static SecondVectorWitness ipc_vector(ipc_vector_expected);
static bool vector_active=false;
static unsigned vector_count=0;
static uint64_t vector_tick=0;
static ColdIpcSnapshot vector_mail{};
struct VectorStop{};
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
static IpcDispatchWitness* ipc_dispatch=nullptr;
static uint32_t dispatch_queue=0;
static unsigned dispatch_count=0;
struct DispatchStop{};
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
static JoinedIpcAck* joined_ack=nullptr;
static nw::CPUContext* joined_cpu=nullptr;
static unsigned joined_count=0;
struct AckReturned{};
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
static LiveEpilogueWitness* epilogue=nullptr;
static NativeIosTransport* epilogue_host=nullptr;
static ExternalReturnWitness reply_capture;
static ColdIpcSnapshot reply_mail{};
static uint32_t reply_request=0,reply_queue=0;
static uint64_t epilogue_tick=0;
static unsigned rfi_count=0,reply_vector_count=0;
static bool reply_vector=false;
struct ReplyEntered{};
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
static JoinedIpcReplyEntry* reply_entry=nullptr;
static nw::CPUContext* reply_cpu=nullptr;
static bool second_dispatch=false;
static unsigned second_dispatch_count=0,reply_entry_count=0;
struct ReplyProcessorReached{};
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
static ReplyProcessorWitness* reply_body=nullptr;
static nw::CPUContext* body_cpu=nullptr;
static unsigned wake_entry_count=0;
struct WakeEntryReached{};
#endif
static NativeIosTransport* submit_host=nullptr;
static nw::CPUContext* submit_cpu=nullptr;
static PostAckSubmitJoin* submit_join=nullptr;
static unsigned submit_stage=0,submit_vectors=0,submit_acks=0;
static unsigned submit_polls=0;
static SecondCompletionAck* si_ack=nullptr;
static unsigned callbacks=0,loop_polls=0,control_writes=0,last_stage=0,last_reason=0,last_trial=0;
struct HarnessFailure:std::runtime_error{unsigned line;explicit HarnessFailure(unsigned n):std::runtime_error("harness assertion"),line(n){}};
struct WitnessFailure:std::runtime_error{WitnessFailure():std::runtime_error("witness refusal"){}};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw HarnessFailure(l.line());
}
static bool device_ok(nw::CPUContext& c){
    return si_ack&&si_ack->token()==3u&&si_ack->postack_device_quiescent(c.inst_count);
}
// The isolated caller and prior SI transaction are seeded, not original
// execution. Exercise actual native SI W1C and the same shared guard used
// by V1235. The subsequent IPC client and all its dependencies are original.
static void seed_completed_si(nw::CPUContext& c,SiController& ctl,SecondCompletionAck& ack){
    constexpr uint32_t A=0x80010000u,Base=0xcd006400u;
    constexpr uint32_t Load=(32u<<26)|(4u<<21)|(3u<<16)|0x34u;
    constexpr uint32_t Store=(36u<<26)|(4u<<21)|(3u<<16)|0x34u;
    constexpr uint32_t Nop=0x60000000u,cfg=SiController::TC_MASK|0x00010300u;
    const std::array<uint8_t,3> response{9,0,0};
    for(unsigned n=0;n<3;++n){
        ctl.write(SiController::Control,cfg|SiController::TSTART);
        ctl.complete(ctl.pending()->token,response);
        if(n!=2)ctl.write(SiController::Control,cfg|SiController::TC_INT);
    }
    c.mmu.write32(A,Load);c.mmu.write32(A+4,Store);c.mmu.write32(A+8,Nop);
    c.msr=0x32u;c.gpr[3]=Base;c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;
    need(ack.arm(ctl,cause,mask,c.inst_count,3,true));
    ++c.inst_count;need(ack.before(c,A,Load,true));
    uint32_t value=0;need(ack.read(ctl,SiController::Control,value));
    c.gpr[4]=value|SiController::TC_INT;++c.inst_count;
    need(ack.before(c,A+4,Store,true)&&ack.write(ctl,SiController::Control,c.gpr[4]));
    ++c.inst_count;need(ack.before(c,A+8,Nop,true)&&ack.resume_after_ack(c,A+8,Nop));
    need(ack.postack_held()&&device_ok(c)&&!(cause.load()&SiController::PI_SI));
}
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
static bool vector_held(nw::CPUContext& c){
    auto s=B::cold_snapshot();
    return vector_active&&s&&same_scheduler_ipc_snapshot(*s,vector_mail)&&device_ok(c);
}
static void vector_refuse(unsigned kind){
    std::cout<<"V1260_VECTOR_REFUSAL kind="<<kind<<" stage="<<ipc_vector.stage()
        <<" reason="<<ipc_vector.failure()<<" gpr="<<ipc_vector.gpr_mask()
        <<" special="<<ipc_vector.special_mask()<<'\n';
    throw WitnessFailure{};
}
void v1260_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!ipc_vector.before(c,pc,w,cause.load(),mask.load(),vector_held(c)))vector_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
static void dispatch_refuse(unsigned kind){
    std::cout<<"V1261_DISPATCH_REFUSAL kind="<<kind<<" stage="<<ipc_dispatch->stage()
        <<" reason="<<ipc_dispatch->failure()<<" reads="<<ipc_dispatch->cause_reads()+ipc_dispatch->mask_reads()
        <<" detail="<<ipc_dispatch->detail()<<" visits="<<ipc_dispatch->visits()<<'\n';
    throw WitnessFailure{};
}
void v1261_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!ipc_dispatch)return; // shared interrupt helpers run earlier
    auto s=B::cold_snapshot();
    const bool guard=std::find(v1261::guard.begin(),v1261::guard.end(),pc)!=v1261::guard.end();
    if(!s||!ipc_dispatch->before(c,pc,w,guard,*s,device_ok(c)))dispatch_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
[[noreturn]]static void body_refuse(unsigned kind){
    std::cout<<"V1282_BODY_REFUSAL kind="<<kind<<" stage="<<reply_body->stage()
        <<" reason="<<reply_body->failure()<<" gate="<<reply_body->gate_failure()
        <<" visits="<<reply_body->visits()<<" reads="<<reply_body->arm_reads()
        <<" invalidations="<<reply_body->invalidations()<<'\n';
    throw WitnessFailure{};
}
void v1281_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(reply_body&&!reply_body->before(c,pc,w,device_ok(c)))body_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
[[noreturn]]static void reply_entry_refuse(unsigned kind){
    std::cout<<"V1275_REPLY_REFUSAL kind="<<kind<<" stage="<<reply_entry->stage()
        <<" reason="<<reply_entry->failure()<<" reads="<<reply_entry->reads()
        <<" visits="<<reply_entry->visits()<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
static void joined_refuse(unsigned kind){
    std::cout<<"V1266_ACK_REFUSAL kind="<<kind<<" stage="<<joined_ack->stage()<<" reason="<<joined_ack->failure()
        <<" gate="<<joined_ack->gate_stage()<<" gate_reason="<<joined_ack->gate_failure()<<" visits="<<joined_ack->visits()<<'\n';
    throw WitnessFailure{};
}
void v1266_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        const bool guard=pc==0x805190c0u||pc==0x8052a51cu||pc==v1255::returned;
        if(!reply_entry->before(c,pc,w,guard,device_ok(c)))reply_entry_refuse(1);
        return;
    }
#endif
    if(!joined_ack)return; // shared original leaves used earlier
    const bool guard=pc==0x805190c0u||pc==0x8052a51cu||pc==v1255::returned;
    if(!joined_ack->before(c,pc,w,guard,device_ok(c)))joined_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
static bool reply_held(nw::CPUContext& c){
    const auto s=B::cold_snapshot();
    using Q=PostAckSchedulerJoin;
    return epilogue_host&&s&&same_scheduler_ipc_snapshot(*s,reply_mail)&&device_ok(c)&&
        c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
        c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read32(Q::Physical)==(Q::Idle&0x3fffffffu)&&
        c.mmu.read16(Q::Thread+712u)==4u&&c.mmu.read32(Q::Thread+732u)==reply_queue&&
        c.mmu.read32(reply_queue)==Q::Thread&&c.mmu.read32(reply_queue+4u)==Q::Thread&&
        epilogue_host->physical_ram().read32(reply_request)==StmIos::Reply&&
        epilogue_host->physical_ram().read32(reply_request+4u)==0u&&
        epilogue_host->physical_ram().read32(reply_request+8u)==StmIos::Open;
}
[[noreturn]]static void epilogue_refuse(unsigned kind){
    std::cout<<"V1271_EPILOGUE_REFUSAL kind="<<kind<<" stage="<<epilogue->stage()<<" reason="<<epilogue->failure()
        <<" entry="<<epilogue->entry_refusal()<<" visits="<<epilogue->visits()<<'\n';
    throw WitnessFailure{};
}
void v1270_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!epilogue)return; // shared IRQ leaves during earlier native execution
    if(!reply_held(c))epilogue_refuse(1);
    if(!epilogue->stage()){
        if(pc!=v1255::returned||c.pc!=pc||!epilogue->begin_pending(c,irq_capture,cause.load(),mask.load()))
            epilogue_refuse(2);
    }
    if(!epilogue->before(c,pc,w,cause.load(),mask.load()))epilogue_refuse(3);
}
#endif
static void submit_trace(uint32_t pc,nw::CPUContext& c){
    need(submit_join);
    const bool ok=submit_join->observe(c,pc,device_ok(c));
    last_stage=submit_join->stage();last_reason=submit_join->failure();
    if(!ok)throw WitnessFailure{};
    submit_stage=submit_join->stage();
    if(pc==OpenScRoute::Vector)++submit_vectors;
    if(submit_stage==8u){
        if(!submit_join->acknowledge(c,device_ok(c))){
            last_reason=submit_join->failure();throw WitnessFailure{};
        }
        need(submit_join->ack_at(c,device_ok(c)));
        ++submit_acks;submit_stage=9u;throw SubmitStop{};
    }
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(witness);
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        if(!reply_body->entry(c,pc,device_ok(c)))body_refuse(2);
        if(reply_body->stage()==2u){++wake_entry_count;throw WakeEntryReached{};}
        return;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        if(!reply_entry->entry(c,pc,device_ok(c)))reply_entry_refuse(2);
        if(reply_entry->stage()==2u){++reply_entry_count;throw ReplyProcessorReached{};}
        return;
    }
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue){
        if(!reply_held(c)||!epilogue->entry(c,pc,cause.load(),mask.load()))epilogue_refuse(4);
        return;
    }
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        if(!joined_ack->entry(c,pc,device_ok(c)))joined_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch){
        auto s=B::cold_snapshot();need(s.has_value());
        if(!ipc_dispatch->stage()){
            const bool begun=
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
                second_dispatch?ipc_dispatch->begin_reply(c,irq_capture,*s,dispatch_queue,reply_request,device_ok(c)):
#endif
                ipc_dispatch->begin(c,irq_capture,*s,dispatch_queue,device_ok(c));
            if(!begun)dispatch_refuse(2);
        }else{
            if(!ipc_dispatch->observe(c,pc,*s,device_ok(c)))dispatch_refuse(3);
            if(ipc_dispatch->stage()==6u){
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
                if(second_dispatch)++second_dispatch_count;else
#endif
                ++dispatch_count;
                throw DispatchStop{};
            }
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
    if(vector_active){
        if(!ipc_vector.stage()){
            if(pc!=ExternalVector||c.inst_count-vector_tick!=1u||
               !ipc_vector.begin_captured(c,irq_capture,cause.load(),mask.load(),vector_held(c)))vector_refuse(2);
        }else{
            if(!ipc_vector.entry(c,pc,cause.load(),mask.load(),vector_held(c)))vector_refuse(3);
            if(ipc_vector.stage()==3u){
#ifdef UNDERCOVER_V1271_IPC_RETURN
                if(reply_vector)++reply_vector_count;else
#endif
                ++vector_count;
                throw VectorStop{};
            }
        }
        return;
    }
#endif
    if(sched_join){
        if(!sched_join->observe(c,pc,device_ok(c))){
            last_stage=sched_join->stage();last_reason=sched_join->failure();throw WitnessFailure{};
        }
        return;
    }
    if(sleep_join){
        if(!sleep_join->observe(c,pc,device_ok(c))){last_stage=sleep_join->stage();last_reason=sleep_join->failure();throw WitnessFailure{};}
        if(sleep_join->stage()==4u){need(sleep_join->select_at(c,device_ok(c)));++sleep_count;throw SleepStop{};}
        return;
    }
    if(submit_host){submit_trace(pc,c);last_stage=submit_stage;return;}
    if(open_witness&&open_witness->stage()){
        if(pc==OpenScRoute::Vector){
            need(open_witness->vector_trace(c,pc,device_ok(c)));++open_vectors;return;
        }
        const bool ok=open_witness->observe(c,pc,device_ok(c));
        last_stage=open_witness->stage();last_reason=open_witness->request_failure();
        if(!ok)throw WitnessFailure{};
        if(last_stage==9u){
            need(open_witness->submit_at(c,device_ok(c)));
            throw RequestReached{};
        }
        return;
    }
    if(stm_witness){
        const bool ok=stm_witness->observe(c,pc,device_ok(c));
        last_stage=stm_witness->stage();last_reason=stm_witness->stm_failure();
        if(!ok)throw WitnessFailure{};
        if(pc==StmPrefixWitness::Stm){++stm_entries;return;}
        if(pc==StmPrefixWitness::Open&&stm_witness->open_at(c)){
            need(open_witness);
            ++open_entries;
            if(!open_witness->begin(c,*stm_witness,device_ok(c))){
                last_reason=open_witness->request_failure();throw WitnessFailure{};
            }
            last_stage=open_witness->stage();return;
        }
        throw WitnessFailure{};
    }
    const bool ok=witness->stage()==2u?witness->target_entry(c,pc,device_ok(c)):witness->continuation(c,pc,device_ok(c));
    last_stage=witness->client_stage();last_reason=witness->cold_failure()?witness->cold_failure():witness->failure();
    if(!ok)throw WitnessFailure{};
}
bool process_pending_callbacks(CPUContext& c){
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        if(!reply_body->poll(c,device_ok(c)))body_refuse(3);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        if(!reply_entry->poll(c,device_ok(c)))reply_entry_refuse(3);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue){
        if(!reply_held(c))epilogue_refuse(5);
        if(!epilogue->stage()){
            if(c.pc!=v1255::returned||c.inst_count!=epilogue_tick)epilogue_refuse(5);
            return false;
        }
        if(epilogue->stage()==2u){
            if(!epilogue->pending_rfi_return(c,cause.load(),mask.load()))epilogue_refuse(6);
            if(!enter_scheduler_reply_irq(c,*epilogue_host,irq_capture,reply_capture,v1259::vector,reply_request))
                epilogue_refuse(7);
            if(!reply_held(c)||c.pc!=ExternalVector)epilogue_refuse(7);
            ++rfi_count;throw ReplyEntered{};
        }
        if(!epilogue->poll(c,cause.load(),mask.load()))epilogue_refuse(5);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        if(!joined_ack->poll(c,device_ok(c)))joined_refuse(3);
        if(c.pc==v1255::returned){
            if(!joined_ack->finish(c,device_ok(c)))joined_refuse(4);
            throw AckReturned{};
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch){
        auto s=B::cold_snapshot();need(s.has_value());
        if(!ipc_dispatch->stage()){
            if(c.pc!=v1260::dispatcher||!same_scheduler_ipc_snapshot(*s,vector_mail)||!device_ok(c))dispatch_refuse(4);
        }else if(!ipc_dispatch->poll(c,*s,device_ok(c)))dispatch_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
    if(vector_active){
        if(!ipc_vector.stage()){
            if(c.pc!=ExternalVector||c.inst_count!=vector_tick||!vector_held(c))vector_refuse(4);
        }else if(!ipc_vector.poll(c,cause.load(),mask.load(),vector_held(c)))vector_refuse(4);
        return false;
    }
#endif
    if(sched_join){
        if(c.pc==v1256::resume&&sched_join->stage()==6u){
            if(!sched_join->enabled_at(c,device_ok(c))){
                last_stage=sched_join->stage();last_reason=sched_join->failure();throw WitnessFailure{};
            }
            ++scheduler_count;throw SchedulerStop{};
        }
        need(sched_join->boundary(c,device_ok(c)));
        const bool allowed=(c.pc==PostAckSchedulerJoin::Select&&sched_join->stage()==1u)||
            sched_join->indirect_poll(c)||
            std::find(v1256::polls.begin(),v1256::polls.end(),c.pc)!=v1256::polls.end();
        if(!allowed){
            last_stage=sched_join->stage();
            std::cout<<"V1256_SCHED_POLL_REFUSAL stage="<<last_stage
                     <<" category="<<(c.pc==PostAckSchedulerJoin::Callback?1:2)<<'\n';
            throw WitnessFailure{};
        }
        return false;
    }
    if(sleep_join){
        need(sleep_join->boundary(c,device_ok(c)));
        need(c.pc==PostAckSleepJoin::Sleep||std::find(v1252::polls.begin(),v1252::polls.end(),c.pc)!=v1252::polls.end());
        return false;
    }
    const auto s=B::cold_snapshot();need(s&&!(s->pi_cause&s->pi_mask)&&!s->queued&&!s->replies);
    if(submit_host){
        need(submit_join->boundary(c,device_ok(c))&&++submit_polls<=8192u);
        if(c.pc==OpenRequestWitness::Submit)need(submit_stage==1&&c.lr==0x80519a3cu);
        else if(c.pc==OpenScRoute::Resume)need(submit_stage==4&&(c.msr&0x8000u));
        else need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        return false;
    }
    if(open_witness&&open_witness->stage()){
        need(open_witness->boundary(c,device_ok(c))&&++open_polls<=8192u);
        // Explicit native tail roots and dispatcher resumes, plus the
        // exact translated local loop and restore polling seams.
        if(c.pc==OpenRequestWitness::Alloc)need(open_witness->stage()==2u&&c.lr==0x8051998cu);
        else if(c.pc==0x8051998cu)need(open_witness->stage()==5u&&c.lr==c.pc&&(c.msr&0x8000u));
        else if(c.pc==v626::restore_resume)need(open_witness->stage()==5u&&(c.msr&0x8000u));
        else if(c.pc==OpenScRoute::Resume)need(open_witness->stage()==7u&&(c.msr&0x8000u));
        else need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        return false;
    }
    if(stm_witness){need(stm_witness->boundary(c,device_ok(c)));return false;}
    need(c.is_running&&!c.dispatch_saved_ctx&&witness&&last_stage>=2&&last_stage<19);
    need(witness->boundary(c,device_ok(c)));
    if(c.pc==v626::restore_resume){
        need((c.msr&0x8000u)&&(last_stage==10u||last_stage==16u));++callbacks;
    }else{
        need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        need(++loop_polls<=8192u);
    }
    return false;
}
bool handle_syscall(CPUContext& c){
    if(submit_host){
        need(submit_stage==4&&submit_join&&device_ok(c));
        need(submit_join->dispatch(c,device_ok(c),[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }));
        return false;
    }

    if(!open_witness||open_witness->stage()!=7u)throw std::runtime_error("V1256 unexpected syscall");
    need(open_witness->dispatch(c,device_ok(c),[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        }));
    ++open_returns;return false;
}
void interpret_step(CPUContext&){throw std::runtime_error("V1256 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V1256 interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V1256 null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V1256 unexpected MMIO16");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V1256 unexpected MMIO16");}
uint32_t HW_Reg_Read32(uint32_t a){
    const auto p=a&0x3fffffffu;
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        auto v=reply_body->read(*body_cpu,a,device_ok(*body_cpu));
        if(!v)body_refuse(4);
        return *v;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        const auto v=reply_entry->read(*reply_cpu,a,device_ok(*reply_cpu));
        if(!v)reply_entry_refuse(4);
        return *v;
    }
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue)epilogue_refuse(8);
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        auto v=joined_ack->read(*joined_cpu,a,device_ok(*joined_cpu));if(!v)joined_refuse(5);return *v;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch){
        if(p!=IosBus::PI_CAUSE&&p!=IosBus::PI_MASK)dispatch_refuse(5);
        B::refresh_pi(a);const auto v=p==IosBus::PI_CAUSE?cause.load():mask.load();
        if(!ipc_dispatch->read(a,v))dispatch_refuse(5);
        return v;
    }
#endif
    if(p==IosBus::PI_MASK)return mask.load();
    if(submit_host&&(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL)){auto v=B::read32(a);need(v.has_value());return *v;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){
        auto v=B::read32(a);need(v.has_value());return *v;
    }
    throw std::runtime_error("V1256 unexpected MMIO read");
}
void HW_Reg_Write32(uint32_t a,uint32_t v){
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        if(!reply_body->write(*body_cpu,a,v,device_ok(*body_cpu)))body_refuse(5);
        return;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){reply_entry->write_refused();reply_entry_refuse(5);}
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue)epilogue_refuse(8);
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        if(!joined_ack->write(*joined_cpu,a,v,device_ok(*joined_cpu)))joined_refuse(6);
        return;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch)dispatch_refuse(6);
#endif
    const auto p=a&0x3fffffffu;
    if(submit_host){
        // The guest CPU is available only in this isolated harness; keep
        // the witness on exactly the same context as the original call.
        need(submit_cpu&&submit_join);
        if(!submit_join->write(*submit_cpu,a,v,device_ok(*submit_cpu))){
            const auto s=B::cold_snapshot();
            const bool ctrl=p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL;
            std::cout<<"V1254_SUBMIT_MMIO_REFUSAL category="<<submit_join->write_failure()
                     <<" writes="<<submit_join->writes()<<" control="<<int(ctrl)
                     <<" low_bits="<<(ctrl?v&0x3fu:0u)<<" prior="<<(s?s->control&0x3fu:0u)<<'\n';
            last_reason=submit_join->failure();throw WitnessFailure{};
        }
        return;
    }
    if(p==IosBus::PI_MASK){mask.store(v);B::refresh_pi(a);return;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){need(B::write32(a,v));return;}
    if(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL){need(B::write32(a,v));++control_writes;return;}
    throw std::runtime_error("V1256 unexpected MMIO write");
}
}
extern "C" void run_game(nw::CPUContext&);
int main(int argc,char** argv)try{
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    need(argc==2);
    const auto initial_data=read_initialized_dol_input(argv[1]);
    std::cout<<"V1264_DOL_DATA verified=1 initialized_only=1 ranges="<<initialized_dol_ranges(initial_data).size()<<'\n';
#else
    (void)argv;need(argc==1);
#endif
    for(unsigned trial=0;trial<8;++trial){
        last_trial=trial;last_stage=last_reason=0;
        auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
        // Match the verified V947 dispatcher setup. Load static initialized
        // data before all modeled OSInit postconditions and original IPC.
        seed_initialized_dol_data(c.mmu,initial_data);
#endif
        cause=0;mask=0xf0|SiController::PI_SI;
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,cause,mask);B binding(host);
        SiController ctl(cause);SecondCompletionAck ack;si_ack=&ack;
        seed_completed_si(c,ctl,ack);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        for(auto w:v626::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v626::submit_sda)c.mmu.write32(w.pc,w.word);
        for(auto w:v1243::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v1252::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v1256::words)c.mmu.write32(w.pc,w.word);
        // Focused fixture: model the default thread previously initialized
        // by OSInitThread, before any original IPC execution.
        c.mmu.write32(PostAckSleepJoin::Current,PostAckSleepJoin::Thread);
        c.mmu.write16(PostAckSleepJoin::Thread+712u,2u);
        c.mmu.write16(PostAckSleepJoin::Thread+714u,1u);
        // Seed only the original V549 thread-init postcondition, before IPC.
        // Neither the saved context nor the idle selection is fabricated.
        using Q=PostAckSchedulerJoin;
        c.mmu.write32(Q::Active,Q::Thread);c.mmu.write32(Q::Physical,Q::Thread&0x3fffffffu);
        c.mmu.write32(0x800000dcu,Q::Thread);c.mmu.write32(0x800000e0u,Q::Thread);
        c.mmu.write32(Q::Thread+720u,16u);c.mmu.write32(Q::Thread+724u,16u);
        c.mmu.write32(Q::Thread+728u,0xffffffffu);
        c.mmu.write32(Q::Thread+772u,0x80751cb8u);c.mmu.write32(Q::Thread+776u,0x80711cb8u);
        c.mmu.write32(0x80711cb8u,0xdeadbabeu);c.mmu.write32(Q::CallbackPtr,Q::Callback);
        // Original initialized SDA/path data is privately seeded before
        // IPC. The actual original IPC code may mutate its own globals.
        for(auto b:v1243::data)c.mmu.write8(b.addr,b.value);
        // The focused fixture seeds the previously installed vector;
        // original cache flush and exception return execute below.
        for(unsigned i=0;i<v626::vector.size();++i){
            c.mmu.write8(OpenScRoute::Source+i,v626::vector[i]);
            c.mmu.write8(OpenScRoute::Vector+i,v626::vector[i]);
        }
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
        // Seed the authenticated prior OSExceptionInit postcondition.
        for(unsigned i=0;i<v1259::vector.size();++i)c.mmu.write8(ExternalVector+i,v1259::vector[i]);
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
        for(unsigned i=0;i<v1260::trampoline_words.size();++i)c.mmu.write32(v1260::trampoline+4u*i,v1260::trampoline_words[i]);
        c.mmu.write32(v1260::dispatcher,v1260::dispatcher_word);
        // Previously installed OS exception-handler metadata, not guest context.
        c.mmu.write32(0x80000048u,0x004e5090u);
        c.mmu.write32(0x80003010u,v1260::trampoline);
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
        for(auto w:v1261::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(W::Sda+v1261::counter_disp,0u);
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
        for(auto w:v1255::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(v1255::returned,v1266::return_word);
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
        for(auto w:v1270::words)c.mmu.write32(w.pc,w.word);
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
        for(auto w:v1281::words)c.mmu.write32(w.pc,w.word);
#endif
        c.guest_flush_count=18000;
        const uint32_t lo=0x93380000u+trial*0x1000u,hi=0x93400000u;
        c.mmu.write32(W::Lo,lo);c.mmu.write32(W::Hi,hi);
        c.mmu.write32(W::Sda-16336u,lo);c.mmu.write32(W::Sda-3352u,hi);
        c.mmu.write32(W::MaskA,0xf7fff7f0u);c.mmu.write32(W::MaskB,0);
        // OSInterruptInit established this pointer in the verified V69 route.
        c.mmu.write32(W::IrqGlobal,W::Table);
        for(unsigned i=0;i<32;++i)c.mmu.write32(W::Table+4*i,i==27?0:0x80005000u+4*i);
        for(unsigned i=0;i<W::HeapLimit+2u;++i)c.mmu.write8(lo-1u+i,uint8_t(0x6b+trial));
        for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+trial*32u+i;
        c.gpr[1]=W::Stack;c.gpr[2]=0x80715ee0u;c.gpr[3]=0;c.gpr[13]=W::Sda;
        c.pc=c.lr=W::Call;c.msr=0x8032u;c.is_running=true;c.dispatch_saved_ctx=0;
        const auto e=v624::expected_client.edges[0];
        PostAckIpcJoin w(v624::expected_client,{W::Call,W::Root,e.branch_word,e.entry_word});witness=&w;
        const bool begun=w.pre_dispatch(c,W::Call,true,device_ok(c));
        last_stage=w.client_stage();last_reason=w.cold_failure()?w.cold_failure():w.failure();
        if(!begun)throw WitnessFailure{};
        // The caller BL is authenticated but its effects are modeled here.
        // Every instruction in the original callee/dependency graph is native.
        ++c.inst_count;
        need(w.before_call(c,W::Call,e.branch_word,true,device_ok(c)));
        c.pc=W::Root;c.lr=W::Return;
        const auto before_callbacks=callbacks,before_writes=control_writes;
        func_805194C4(c);
        need(c.pc==W::Return&&c.lr==W::Return&&c.is_running);
        const bool returned=w.continuation(c,c.pc,device_ok(c));last_stage=w.client_stage();last_reason=w.cold_failure()?w.cold_failure():w.failure();
        if(!returned)throw WitnessFailure{};
        need(w.stage()==5u&&w.client_stage()==19u&&w.heap_size()>0&&host.serviced_steps()==0);
        need(device_ok(c)&&ctl.issued_tokens()==3u&&!ctl.pending());
        need(callbacks==before_callbacks+2&&control_writes==before_writes+1);
        PostAckStmJoin stm(v629::expected_stm);stm_witness=&stm;
        PostAckOpenJoin open(v639::expected_open,v626::vector);open_witness=&open;open_polls=0;
        need(stm.begin(c,w,device_ok(c)));
        // Focused proof: model the caller bridge after the verified IPC
        // return. Execute the original STM prefix, not a synthetic
        // pathname selection. Do not claim the OSInit bridge executed.
        c.inst_count+=7;c.pc=StmPrefixWitness::Stm;c.lr=v629::expected_stm.stm.lr;
        bool stopped=false;
        try{run_game(c);}catch(const RequestReached&){stopped=true;}
        need(stopped&&stm.stage()==3u&&open.stage()==9u&&open.submit_at(c,device_ok(c))&&host.serviced_steps()==0);
        need(open.request()&&open.path_kind()==stm.path_kind()&&open_vectors==trial+1u&&open_returns==trial+1u);
        std::cout<<"V1256_OPEN_TRIAL n="<<trial<<" path="<<open.path_kind()<<" request=1 native_rfi=1 serviced=0\n";
        // Continue from the authenticated native submit entry, without
        // resetting memory or creating a replacement guest request.
        const auto kind=open.path_kind();
        std::array<VectorEdge,v626::submit_edges.size()> edges{};
        for(unsigned i=0;i<edges.size();++i){auto e=v626::submit_edges[i];edges[i]={e.pc,e.lr,e.branch,e.entry};}
        PostAckSubmitJoin next(edges,v626::vector);
        need(next.begin(c,open,device_ok(c)));
        open_witness=nullptr;stm_witness=nullptr;
        submit_host=&host;submit_join=&next;submit_cpu=&c;submit_stage=1;submit_polls=0;
        bool acked=false;
        try{run_game(c);}catch(const SubmitStop&){acked=true;}
        need(acked&&submit_stage==9&&submit_acks==trial+1&&submit_vectors==trial+1&&host.serviced_steps()==1&&device_ok(c));
        need(ctl.issued_tokens()==3u&&!ctl.pending());
        std::cout<<"V1256_SUBMIT_TRIAL n="<<trial<<" path="<<kind<<" ack=1 reply=0 si_quiescent=1\n";
        PostAckSleepJoin sleep(v1252::edges);
        need(sleep.begin(c,next,device_ok(c)));
        submit_host=nullptr;submit_join=nullptr;submit_cpu=nullptr;
        sleep_join=&sleep;bool waiting=false;
        try{run_game(c);}catch(const SleepStop&){waiting=true;}
        need(waiting&&sleep.stage()==4u&&sleep.select_at(c,device_ok(c))&&host.serviced_steps()==1u&&sleep_count==trial+1u);
        std::cout<<"V1252_SLEEP_TRIAL n="<<trial<<" waiting=1 queue=1 pending_ack=1 reply=0\n";
        PostAckSchedulerJoin sched(v1256::edges,v1256::indirect,v1256::resume,v1256::resume_word);
        need(sched.begin(c,sleep,device_ok(c)));sleep_join=nullptr;sched_join=&sched;
        bool enabled=false;
        try{run_game(c);}catch(const SchedulerStop&){enabled=true;}
        need(enabled&&sched.stage()==7u&&scheduler_count==trial+1u&&host.serviced_steps()==1u&&device_ok(c));
        need(host.exception_pending(c.msr)&&c.pc==v1256::resume&&(c.msr&0x8000u));
        std::cout<<"V1256_SCHED_TRIAL n="<<trial<<" saved=1 idle=1 enabled=1 pending_ack=1 irq_entered=0\n";
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
        const auto before_irq=c.inst_count;
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
        irq_capture=ExternalReturnWitness{};ipc_vector=SecondVectorWitness(ipc_vector_expected);
        need(irq_capture.capture(c,cause.load(),mask.load(),H::PI_HOLLYWOOD));
        vector_mail=host.cold_ipc_snapshot();vector_tick=c.inst_count;
#endif
        need(enter_scheduler_ipc_irq(c,host,v1259::vector,next.request()&0x3fffffffu));
        need(c.pc==ExternalVector&&c.srr0==v1256::resume&&c.inst_count==before_irq&&
             c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread&&
             host.serviced_steps()==1u&&device_ok(c));
        ++irq_count;
        std::cout<<"V1259_IRQ_TRIAL n="<<trial<<" entered=1 srr=1 registers=1 pending_ack=1 vector_executed=0\n";
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
        vector_active=true;sched_join=nullptr;bool dispatched=false;
        try{run_game(c);}catch(const VectorStop&){dispatched=true;}
        need(dispatched&&ipc_vector.stage()==3u&&vector_count==trial+1u&&vector_held(c)&&
             c.pc==v1260::dispatcher&&irq_capture.saved_integer(c,Q::Idle).ok()&&
             c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread);
        vector_active=false;
        std::cout<<"V1260_VECTOR_TRIAL n="<<trial<<" saved_fields=38 original_vector=1 trampoline=1 pending_ack=1 dispatcher_executed=0\n";
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
        IpcDispatchWitness dispatch({v1261::code,v1261::handler,Q::Idle,Q::Thread,W::Table,W::IrqGlobal,W::Sda+v1261::counter_disp});
        ipc_dispatch=&dispatch;dispatch_queue=sleep.queue();bool handler_reached=false;
        try{run_game(c);}catch(const DispatchStop&){handler_reached=true;}
        need(handler_reached&&dispatch.stage()==6u&&dispatch_count==trial+1u&&
             dispatch.cause_reads()&&dispatch.mask_reads()&&c.pc==v1261::handler&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&device_ok(c));
        ipc_dispatch=nullptr;
        std::cout<<"V1261_DISPATCH_TRIAL n="<<trial<<" original_dispatcher=1 index=27 context=1 pi_reads=1 handler_entry=1 handler_executed=0\n";
#ifdef UNDERCOVER_V1266_JOINED_ACK
        JoinedIpcAck joined(v1255::handler,v1255::returned,v1266::return_word,v1266::final_blr,Q::Idle,Q::Thread,v1255::edges,v1255::polls);
        need(joined.begin(c,dispatch,irq_capture,sleep.queue(),next.request()&0x3fffffffu,kind,device_ok(c)));
        joined_ack=&joined;joined_cpu=&c;
        bool ack_returned=false;
        try{run_game(c);}catch(const AckReturned&){ack_returned=true;}
        need(ack_returned&&joined.stage()==2u&&host.serviced_steps()==1u);
        if(!joined.publish(c,device_ok(c)))joined_refuse(7);
        need(joined.stage()==3u&&host.serviced_steps()==2u&&c.pc==v1255::returned&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u);
        ++joined_count;joined_ack=nullptr;joined_cpu=nullptr;
        std::cout<<"V1266_ACK_TRIAL n="<<trial<<" handler_return=1 guest_w1c=1 native_reply=1 waiting=1 saved_fields=38\n";
#ifdef UNDERCOVER_V1271_IPC_RETURN
        // Preserve the live handler return and native reply. The original
        // dispatcher suffix executes with no host scheduler/context edits.
        LiveEpilogueWitness live(v1270::expected(Q::Idle));
        epilogue=&live;epilogue_host=&host;reply_mail=host.cold_ipc_snapshot();
        reply_request=next.request()&0x3fffffffu;reply_queue=sleep.queue();
        epilogue_tick=c.inst_count;reply_capture=ExternalReturnWitness{};
        bool reentered=false;
        try{run_game(c);}catch(const ReplyEntered&){reentered=true;}
        need(reentered&&live.stage()==3u&&rfi_count==trial+1u&&irq_capture.stage()==3u&&
             reply_capture.stage()==1u&&reply_held(c)&&host.serviced_steps()==2u);
        epilogue=nullptr;epilogue_host=nullptr;
        std::cout<<"V1271_RFI_TRIAL n="<<trial<<" original_scheduler=1 native_rfi=1 restored=1 reply_irq=1 waiting=1\n";
        // The second vector uses its own capture, not the previous saved
        // context as an artificial substitute for native vector stores.
        irq_capture=reply_capture;ipc_vector=SecondVectorWitness(ipc_vector_expected);
        vector_mail=host.cold_ipc_snapshot();vector_tick=c.inst_count;
        reply_vector=true;vector_active=true;bool reply_dispatched=false;
        try{run_game(c);}catch(const VectorStop&){reply_dispatched=true;}
        need(reply_dispatched&&ipc_vector.stage()==3u&&reply_vector_count==trial+1u&&
             vector_held(c)&&c.pc==v1260::dispatcher&&irq_capture.saved_integer(c,Q::Idle).ok()&&
             c.mmu.read16(Q::Thread+712u)==4u&&c.mmu.read32(sleep.queue())==Q::Thread&&
             c.mmu.read32(sleep.queue()+4u)==Q::Thread&&host.serviced_steps()==2u);
        vector_active=false;reply_vector=false;
        std::cout<<"V1271_REPLY_VECTOR_TRIAL n="<<trial<<" original_vector=1 trampoline=1 saved_fields=38 pending_reply=1 dispatcher_executed=0\n";
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
        IpcDispatchWitness second({v1261::code,v1261::handler,Q::Idle,Q::Thread,W::Table,W::IrqGlobal,W::Sda+v1261::counter_disp});
        need(c.mmu.read32(W::Sda+v1261::counter_disp)==0u);
        ipc_dispatch=&second;dispatch_queue=sleep.queue();second_dispatch=true;
        bool second_reached=false;
        try{run_game(c);}catch(const DispatchStop&){second_reached=true;}
        need(second_reached&&second.stage()==6u&&second.reply_mode()&&second_dispatch_count==trial+1u&&
             second.cause_reads()&&second.mask_reads()&&c.pc==v1261::handler&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&device_ok(c));
        ipc_dispatch=nullptr;second_dispatch=false;
        std::cout<<"V1275_REPLY_DISPATCH_TRIAL n="<<trial<<" dispatcher=1 index=27 handler_entry=1 pending_reply=1\n";
        constexpr uint32_t ReadLeaf=0x8051905cu,Reply=0x805190c0u,ReplyReturn=0x80519354u;
        auto match=[](const auto& e){return e.pc==Reply&&e.lr==ReplyReturn;};
        need(std::count_if(v1255::edges.begin(),v1255::edges.end(),match)==1);
        auto e=*std::find_if(v1255::edges.begin(),v1255::edges.end(),match);
        JoinedIpcReplyEntry entry(v1255::handler,ReadLeaf,e,Q::Idle,Q::Thread,v1255::edges,v1255::polls);
        need(entry.begin(c,second,irq_capture,sleep.queue(),reply_request,device_ok(c)));
        reply_entry=&entry;reply_cpu=&c;bool processor_reached=false;
        try{run_game(c);}catch(const ReplyProcessorReached&){processor_reached=true;}
        need(processor_reached&&entry.stage()==2u&&entry.reads()&&reply_entry_count==trial+1u&&
             c.pc==Reply&&c.lr==ReplyReturn&&host.serviced_steps()==2u&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread);
        reply_entry=nullptr;reply_cpu=nullptr;
        std::cout<<"V1275_REPLY_ENTRY_TRIAL n="<<trial<<" original_handler=1 reply_processor_entry=1 pending_reply=1 waiting=1\n";
#ifdef UNDERCOVER_V1282_REPLY_WAKE
        // Continue the live processor call. No scheduler registers,
        // request buffer or queue links are changed by the host.
        ReplyProcessorWitness body(v1281::expected(Q::Idle,Q::Thread));
        reply_body=&body;body_cpu=&c;
        if(!body.begin(c,entry,irq_capture,sleep.queue(),reply_request,device_ok(c)))body_refuse(6);
        bool wake_reached=false;
        try{run_game(c);}catch(const WakeEntryReached&){wake_reached=true;}
        const auto consumed=host.cold_ipc_snapshot();
        need(wake_reached&&body.stage()==2u&&wake_entry_count==trial+1u&&body.arm_reads()&&body.invalidations()&&
             c.pc==0x8052a51cu&&c.lr==0x805192d4u&&c.gpr[3]==sleep.queue()&&
             !(consumed.control&(M::X1|M::Y1|M::Y2))&&consumed.steps==2u&&!consumed.replies&&
             consumed.ppc==reply_request&&consumed.arm==reply_request&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread&&
             device_ok(c));
        reply_body=nullptr;body_cpu=nullptr;
        std::cout<<"V1282_WAKE_ENTRY_TRIAL n="<<trial<<" original_processor=1 armmsg=1 native_dcbi=1 y1_w1c=1 queue=1 wake_executed=0\n";
#endif
#endif
#endif
#endif
#endif
#endif
#endif
        sched_join=nullptr;witness=nullptr;si_ack=nullptr;
    }
    need(callbacks==16&&control_writes==8&&stm_entries==8&&open_entries==8);
    std::cout<<"V1256_OPEN_POLLS restore=16 backward="<<loop_polls<<"\n";
    std::cout<<"V1256_SCHED_NATIVE owner=1 trials=8 submitted=8 ack=8 waiting=8 saved=8 idle=8 ee=8 pending_irq=8 irq_entered=0 reply=0 seeded_thread=1 synthetic_ack=1 synthetic_caller=1 synthetic_bridge=1 seeded_vector=1 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
    need(irq_count==8u);
    std::cout<<"V1259_IRQ_NATIVE owner=1 trials=8 entered=8 saved=8 idle=8 pending_ack=8 vector_executed=0 reply=0 seeded_vector=1 fallback=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
    need(vector_count==8u);
    std::cout<<"V1260_VECTOR_NATIVE owner=1 trials=8 original_vector=8 trampoline=8 saved_fields=38 dispatcher_entry=8 dispatcher_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    need(dispatch_count==8u);
    std::cout<<"V1261_DISPATCH_NATIVE owner=1 trials=8 dispatcher=8 ipc_index=27 handler_entry=8 handler_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1266_JOINED_ACK
    need(joined_count==8u);
    std::cout<<"V1266_ACK_NATIVE owner=1 trials=8 original_dispatch=8 original_handler_return=8 native_reply=8 waiting=8 saved_fields=38 modeled_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1271_IPC_RETURN
    need(rfi_count==8u&&reply_vector_count==8u);
    std::cout<<"V1271_REPLY_VECTOR_NATIVE owner=1 trials=8 first_rfi=8 restored=8 reply_irq=8 original_vector=8 trampoline=8 saved_fields=38 second_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    need(second_dispatch_count==8u&&reply_entry_count==8u);
    std::cout<<"V1275_REPLY_ENTRY_NATIVE owner=1 trials=8 original_second_dispatch=8 original_reply_handler=8 reply_processor_entry=8 waiting=8 ios_steps=2 wakeup=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    need(wake_entry_count==8u);
    std::cout<<"V1282_REPLY_WAKE_NATIVE owner=1 trials=8 original_processor=8 armmsg=8 native_dcbi=8 y1_w1c=8 original_wake_entry=8 waiting=8 ios_steps=2 wake_executed=0 fallback=0 complete_image=0 boot_verified=0\n";
#endif
#endif
#endif
#endif
#endif
#endif
#endif
}catch(const WitnessFailure&){
    std::cout<<"V1256_OPEN_FAILURE kind=witness trial="<<last_trial<<" stage="<<last_stage<<" reason="<<last_reason<<" line=0\n";return 1;
}catch(const HarnessFailure& e){
    std::cout<<"V1256_OPEN_FAILURE kind=assertion trial="<<last_trial<<" stage="<<last_stage<<" reason=0 line="<<e.line<<"\n";return 1;
}catch(const std::exception& e){
    const std::string_view msg=e.what();
    const char* kind="other";
    if(msg=="V1256 interpreter forbidden")kind="interpreter";
    else if(msg=="V1256 unexpected syscall")kind="syscall";
    else if(msg=="V1256 null branch")kind="null_branch";
    else if(msg=="V1256 unexpected MMIO16"||msg=="V1256 unexpected MMIO read"||msg=="V1256 unexpected MMIO write")kind="mmio";
    else if(msg=="unexpected cold IPC control write"||msg=="cold IPC proof already rejected")kind="mailbox";
    std::cout<<"V1256_OPEN_FAILURE kind="<<kind<<" trial="<<last_trial<<" stage="<<last_stage<<" reason=0 line=0\n";return 1;
}
