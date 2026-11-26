#include "runtime/cpu_context.h"
#include "functions.h"
#include "v624_private_ipc_expectations.h"
#include "v626_private_words.h"
#include "wii_post_ack_open_join_v1242.h"
#include "v639_private_open_expectations.h"
#include "v629_private_stm_expectations.h"
#include "v1243_private_stm_data.h"
#include "wii_second_completion_ack_v950.h"
#include "wii_cold_open_reply_gate_v1253.h"
#include "v1255_private_ack.h"
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
struct RequestReached{};struct SubmitStop{};
static NativeIosTransport* submit_host=nullptr;
static OpenScRoute* submit_route=nullptr;
static unsigned submit_stage=0,submit_writes=0,submit_vectors=0,submit_acks=0,submit_kind=0;
static uint32_t submit_request=0,submit_path=0;
static uint64_t submit_tick=0;
static unsigned submit_polls=0;
static ColdOpenReplyGate* reply_gate=nullptr;
static nw::CPUContext* ack_cpu=nullptr;
static unsigned handler_entries=0,handler_reads=0,handler_replies=0;
static uint64_t handler_tick=0;
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
static void submit_trace(uint32_t pc,nw::CPUContext& c){
    using R=OpenScRoute;using S=StmIos;
    need(submit_host&&submit_route&&device_ok(c)&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.inst_count>=submit_tick&&c.inst_count-submit_tick<200000u);
    if(pc==R::Vector){need(submit_stage==4&&submit_route->vector_trace(pc,c));++submit_vectors;return;}
    if(pc==OpenRequestWitness::Submit){need(submit_stage==1&&c.lr==0x80519a3cu);return;}
    if(pc==R::Call){
        need(submit_stage==3&&c.lr==R::SubmitCaller&&c.open_cache_range.ready_sc(c));
        submit_route->arm(pc,c);submit_stage=4;return;
    }
    if(pc==R::SubmitCaller){
        need(submit_stage==4&&submit_route->returned(c)&&c.open_cache_range.finish(c));
        submit_stage=5;return;
    }
    const auto it=std::find_if(v626::submit_edges.begin(),v626::submit_edges.end(),[&](const auto& e){return e.pc==pc&&e.lr==c.lr;});
    need(it!=v626::submit_edges.end()&&c.pc==pc&&c.mmu.read32(pc)==it->entry&&c.mmu.read32(c.lr-4)==it->branch);
    if(pc==0x805293b0u){need(submit_stage==1);submit_stage=2;return;}
    if(pc==R::Call-40u){
        need(submit_stage==2&&c.lr==R::SubmitCaller&&(c.msr&0x8000u));
        const uint32_t a=c.gpr[3]&0x3fffffffu,n=c.gpr[4];
        need(n>=32&&n<=0x1000&&a<=submit_request&&uint64_t(a)+n>=uint64_t(submit_request)+32);
        c.open_cache_range=OpenCacheRangeTrace{};
        need(c.open_cache_range.begin(c,c.gpr[3],n));submit_stage=3;return;
    }
    if(pc==OpenRequestWitness::Disable){need(submit_stage==5&&(c.msr&0x8000u));submit_stage=6;return;}
    if(pc==0x8051afe0u){need(submit_stage==6&&!(c.msr&0x8000u));submit_stage=7;return;}
    if(pc==0x8051906cu||pc==0x8051905cu){need(submit_stage==7&&!(c.msr&0x8000u));return;}
    if(pc==0x8052a430u){
        const auto before=B::cold_snapshot();auto& ram=submit_host->physical_ram();
        need(submit_stage==7&&submit_writes==2&&!(c.msr&0x8000u)&&before&&before->queued&&before->ppc==submit_request&&
             (before->control&M::X1)&&!(before->control&(M::Y1|M::Y2))&&!before->steps&&!before->replies&&!(before->pi_cause&before->pi_mask));
        need(ram.valid(submit_request,64)&&!(submit_request&31u)&&ram.read32(submit_request)==S::Open&&
             ram.read32(submit_request+12)==submit_path&&ram.read32(submit_request+16)==0);
        const auto ack=B::service_at_guest_boundary(c.msr);const auto after=B::cold_snapshot();
        const auto device=submit_kind==1?S::Device::Immediate:S::Device::Event;
        need(ack&&ack->progress==S::Pump::Ack&&ack->broadway_irq_level&&!ack->guest_exception_ready&&after&&
             !after->queued&&after->steps==1&&after->replies==1&&!(after->control&(M::X1|M::Y1))&&(after->control&M::Y2)&&
             (after->flags&H::IPC_PPC)&&(after->pi_cause&H::PI_HOLLYWOOD)&&submit_host->services().is_open(0,device)&&
             ram.read32(submit_request)==S::Open&&device_ok(c));
        ++submit_acks;submit_stage=8;throw SubmitStop{};
    }
    need(false);
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(witness);
    if(reply_gate){
        need(ack_cpu==&c&&device_ok(c)&&!(c.msr&0x8000u)&&c.inst_count>=handler_tick&&c.inst_count-handler_tick<8192u&&reply_gate->boundary(true));
        if(pc==v1255::handler){
            need(c.lr==v1255::returned&&c.gpr[3]==27u&&c.gpr[4]==0x806f5730u);
            ++handler_entries;return;
        }
        need(pc==0x8051905cu||pc==0x8051906cu||pc==0x8051b060u);
        auto it=std::find_if(v1255::edges.begin(),v1255::edges.end(),[&](const auto& e){return e.pc==pc&&e.lr==c.lr;});
        need(it!=v1255::edges.end()&&c.mmu.read32(pc)==it->entry_word&&c.mmu.read32(c.lr-4)==it->branch_word);
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
    if(reply_gate){
        need(ack_cpu==&c&&device_ok(c)&&!(c.msr&0x8000u)&&reply_gate->boundary(true));
        need(std::find(v1255::polls.begin(),v1255::polls.end(),c.pc)!=v1255::polls.end());
        return false;
    }
    const auto s=B::cold_snapshot();need(s&&!(s->pi_cause&s->pi_mask)&&!s->queued&&!s->replies);
    if(submit_host){
        need(device_ok(c)&&++submit_polls<=8192u);
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
        need(submit_stage==4&&submit_route&&device_ok(c));
        need(submit_route->dispatch(c,[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }));
        return false;
    }

    if(!open_witness||open_witness->stage()!=7u)throw std::runtime_error("V1255 unexpected syscall");
    need(open_witness->dispatch(c,device_ok(c),[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        }));
    ++open_returns;return false;
}
void interpret_step(CPUContext&){throw std::runtime_error("V1255 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V1255 interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V1255 null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V1255 unexpected MMIO16");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V1255 unexpected MMIO16");}
uint32_t HW_Reg_Read32(uint32_t a){
    const auto p=a&0x3fffffffu;
    if(reply_gate){
        need(ack_cpu&&reply_gate->boundary(device_ok(*ack_cpu)));
        need(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL||
             p==IosBus::IPC+H::PPC_FLAG||p==IosBus::MIRROR+H::PPC_FLAG);
        auto v=B::read32(a);need(v.has_value());++handler_reads;return *v;
    }
    if(p==IosBus::PI_MASK)return mask.load();
    if(submit_host&&(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL)){auto v=B::read32(a);need(v.has_value());return *v;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){
        auto v=B::read32(a);need(v.has_value());return *v;
    }
    throw std::runtime_error("V1255 unexpected MMIO read");
}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    const auto p=a&0x3fffffffu;
    if(reply_gate){
        need(ack_cpu);
        if(!reply_gate->write(a,v,ack_cpu->msr,device_ok(*ack_cpu))){
            const auto s=B::cold_snapshot();
            const bool ctrl=p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL;
            std::cout<<"V1255_ACK_REFUSAL stage="<<reply_gate->stage()<<" reason="<<reply_gate->failure()
                     <<" control="<<int(ctrl)<<" low_bits="<<(ctrl?v&63u:0u)<<" prior="<<(s?s->control&63u:0u)<<'\n';
            last_stage=reply_gate->stage();last_reason=reply_gate->failure();throw WitnessFailure{};
        }
        return;
    }
    if(submit_host){
        need(submit_stage==7);
        if(p==IosBus::IPC+M::PPCMSG||p==IosBus::MIRROR+M::PPCMSG)need(submit_writes==0&&v==submit_request);
        else if(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL)need(submit_writes==1&&(v&M::X1));
        else need(false);
        need(B::write32(a,v));++submit_writes;return;
    }
    if(p==IosBus::PI_MASK){mask.store(v);B::refresh_pi(a);return;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){need(B::write32(a,v));return;}
    if(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL){need(B::write32(a,v));++control_writes;return;}
    throw std::runtime_error("V1255 unexpected MMIO write");
}
}
extern "C" void run_game(nw::CPUContext&);
int main()try{
    for(unsigned trial=0;trial<8;++trial){
        last_trial=trial;last_stage=last_reason=0;
        auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
        cause=0;mask=0xf0|SiController::PI_SI;
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,cause,mask);B binding(host);
        SiController ctl(cause);SecondCompletionAck ack;si_ack=&ack;
        seed_completed_si(c,ctl,ack);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        for(auto w:v626::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v626::submit_sda)c.mmu.write32(w.pc,w.word);
        for(auto w:v1243::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v1255::words)c.mmu.write32(w.pc,w.word);
        // Original initialized SDA/path data is privately seeded before
        // IPC. The actual original IPC code may mutate its own globals.
        for(auto b:v1243::data)c.mmu.write8(b.addr,b.value);
        // The focused fixture seeds the previously installed vector;
        // original cache flush and exception return execute below.
        for(unsigned i=0;i<v626::vector.size();++i){
            c.mmu.write8(OpenScRoute::Source+i,v626::vector[i]);
            c.mmu.write8(OpenScRoute::Vector+i,v626::vector[i]);
        }
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
        std::cout<<"V1255_OPEN_TRIAL n="<<trial<<" path="<<open.path_kind()<<" request=1 native_rfi=1 serviced=0\n";
        // Continue from the authenticated native submit entry, without
        // resetting memory or creating a replacement guest request.
        const auto kind=open.path_kind(),path=c.mmu.read32(open.request()+12u)&0x3fffffffu;
        need(open.submit_at(c,device_ok(c))&&path);
        open_witness=nullptr;stm_witness=nullptr;
        OpenScRoute next(v626::vector,OpenScRoute::SubmitCaller);
        submit_host=&host;submit_route=&next;submit_stage=1;submit_writes=submit_polls=0;
        submit_request=open.request()&0x3fffffffu;submit_path=path;submit_kind=kind;submit_tick=c.inst_count;
        bool acked=false;
        try{run_game(c);}catch(const SubmitStop&){acked=true;}
        need(acked&&submit_stage==8&&submit_acks==trial+1&&submit_vectors==trial+1&&host.serviced_steps()==1&&device_ok(c));
        need(ctl.issued_tokens()==3u&&!ctl.pending());
        std::cout<<"V1255_SUBMIT_TRIAL n="<<trial<<" path="<<kind<<" ack=1 reply=0 si_quiescent=1\n";
        submit_host=nullptr;submit_route=nullptr;
        // Isolated IRQ handler call: the original submit and native ACK
        // really occurred, but sleep, vector and dispatch are not run.
        // Do not alter the original guest request or mailbox state.
        ColdOpenReplyGate gate;need(gate.begin(submit_request,kind,device_ok(c)));
        c.pc=v1255::handler;c.lr=v1255::returned;c.ctr=v1255::handler;
        c.gpr[3]=27u;c.gpr[4]=0x806f5730u;
        const auto saved=c.gpr;const auto saved_msr=c.msr;
        reply_gate=&gate;ack_cpu=&c;handler_tick=c.inst_count;
        const auto reads_before=handler_reads;
        func_80519318(c);
        need(c.pc==v1255::returned&&c.lr==v1255::returned&&c.msr==saved_msr&&c.gpr[1]==saved[1]&&c.gpr[2]==saved[2]);
        for(unsigned i=13;i<32;++i)need(c.gpr[i]==saved[i]);
        need(handler_entries==trial+1u&&handler_reads>reads_before&&gate.stage()==3u&&gate.boundary(device_ok(c)));
        need(gate.publish(c.msr,device_ok(c))&&gate.reply_pending(true)&&host.serviced_steps()==2u);
        ++handler_replies;
        std::cout<<"V1255_ACK_TRIAL n="<<trial<<" handler_return=1 ack_cleared=1 native_reply=1 si_quiescent=1\n";
        reply_gate=nullptr;ack_cpu=nullptr;witness=nullptr;si_ack=nullptr;
    }
    need(callbacks==16&&control_writes==8&&stm_entries==8&&open_entries==8&&handler_replies==8);
    std::cout<<"V1255_OPEN_POLLS restore=16 backward="<<loop_polls<<"\n";
    std::cout<<"V1255_ACK_NATIVE owner=1 trials=8 submitted=8 ack=8 handler_return=8 reply=8 native_rfi=16 si_quiescent=8 modeled_dispatch=1 sleep_executed=0 wakeup=0 synthetic_ack=1 synthetic_caller=1 synthetic_bridge=1 seeded_vector=1 fallback=0 complete_image=0 boot_verified=0\n";
}catch(const WitnessFailure&){
    std::cout<<"V1255_OPEN_FAILURE kind=witness trial="<<last_trial<<" stage="<<last_stage<<" reason="<<last_reason<<" line=0\n";return 1;
}catch(const HarnessFailure& e){
    std::cout<<"V1255_OPEN_FAILURE kind=assertion trial="<<last_trial<<" stage="<<last_stage<<" reason=0 line="<<e.line<<"\n";return 1;
}catch(const std::exception& e){
    const std::string_view msg=e.what();
    const char* kind="other";
    if(msg=="V1255 interpreter forbidden")kind="interpreter";
    else if(msg=="V1255 unexpected syscall")kind="syscall";
    else if(msg=="V1255 null branch")kind="null_branch";
    else if(msg=="V1255 unexpected MMIO16"||msg=="V1255 unexpected MMIO read"||msg=="V1255 unexpected MMIO write")kind="mmio";
    else if(msg=="unexpected cold IPC control write"||msg=="cold IPC proof already rejected")kind="mailbox";
    std::cout<<"V1255_OPEN_FAILURE kind="<<kind<<" trial="<<last_trial<<" stage="<<last_stage<<" reason=0 line=0\n";return 1;
}
