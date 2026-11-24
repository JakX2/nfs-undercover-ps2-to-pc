#include "runtime/cpu_context.h"
#include "functions.h"
#include "v624_private_ipc_expectations.h"
#include "v626_private_words.h"
#include "v639_private_open_expectations.h"
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
static W* witness=nullptr;
static OpenRequestWitness* open_witness=nullptr;
static OpenScRoute* sc_route=nullptr;
static unsigned open_stage=0,open_reason=0,open_vectors=0,open_returns=0,open_polls=0;
struct OpenStop{};struct SubmitStop{};
static NativeIosTransport* submit_host=nullptr;
static OpenScRoute* submit_route=nullptr;
static unsigned submit_stage=0,submit_writes=0,submit_vectors=0,submit_acks=0,submit_kind=0;
static uint32_t submit_request=0,submit_path=0;
static uint64_t submit_tick=0;
static unsigned submit_polls=0;
static unsigned callbacks=0,loop_polls=0,control_writes=0,last_stage=0,last_reason=0,last_trial=0;
struct HarnessFailure:std::runtime_error{unsigned line;explicit HarnessFailure(unsigned n):std::runtime_error("harness assertion"),line(n){}};
struct WitnessFailure:std::runtime_error{WitnessFailure():std::runtime_error("witness refusal"){}};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw HarnessFailure(l.line());
}
static void submit_trace(uint32_t pc,nw::CPUContext& c){
    using R=OpenScRoute;using S=StmIos;
    need(submit_host&&submit_route&&c.is_running&&!c.dispatch_saved_ctx&&c.inst_count-submit_tick<200000u);
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
             ram.read32(submit_request)==S::Open);
        ++submit_acks;submit_stage=8;throw SubmitStop{};
    }
    need(false);
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    if(submit_host){submit_trace(pc,c);return;}
    if(open_witness){
        if(pc==OpenRequestWitness::Open)return;
        if(pc==OpenScRoute::Vector){need(sc_route->vector_trace(pc,c));++open_vectors;return;}
        const bool ok=open_witness->observe(pc,c,*sc_route);
        open_stage=open_witness->stage();open_reason=open_witness->failure();
        if(!ok)throw WitnessFailure{};
        if(open_stage==9)throw OpenStop{};
        return;
    }
    need(witness);
    const bool ok=witness->observe(pc,c);
    last_stage=witness->stage();last_reason=witness->failure();
    if(!ok)throw WitnessFailure{};
}
bool process_pending_callbacks(CPUContext& c){
    const auto s=B::cold_snapshot();need(s&&!(s->pi_cause&s->pi_mask)&&!s->queued&&!s->replies);
    need(c.is_running&&!c.dispatch_saved_ctx&&witness&&last_stage>=1);
    if(submit_host){
        need(++submit_polls<=8192u);
        if(c.pc==OpenRequestWitness::Submit)need(submit_stage==1&&c.lr==0x80519a3cu);
        else if(c.pc==OpenScRoute::Resume)need(submit_stage==4&&(c.msr&0x8000u));
        else need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        return false;
    }
    if(open_witness){
        need(++open_polls<=8192u);
        // run_game polls before every dispatched root/resume, in addition
        // to the exact generated backward-loop and MSR callback seams.
        if(c.pc==OpenRequestWitness::Open)need(open_stage==1&&c.lr==0x8052b090u);
        else if(c.pc==OpenRequestWitness::Alloc)need(open_stage==2&&c.lr==0x8051998cu);
        else if(c.pc==0x8051998cu)need(open_stage==5&&c.lr==c.pc&&(c.msr&0x8000u));
        else if(c.pc==v626::restore_resume)need(open_stage==5&&(c.msr&0x8000u));
        else if(c.pc==OpenScRoute::Resume)need(open_stage==7&&(c.msr&0x8000u));
        else need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        return false;
    }
    need(last_stage<19);
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
        need(submit_stage==4&&submit_route);
        need(submit_route->dispatch(c,[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }));
        return false;
    }
    need(open_witness&&open_stage==7&&sc_route);
    need(sc_route->dispatch(c,[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        }));
    ++open_returns;return false;
}
void interpret_step(CPUContext&){throw std::runtime_error("V626 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V626 interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V626 null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V626 unexpected MMIO16");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V626 unexpected MMIO16");}
uint32_t HW_Reg_Read32(uint32_t a){
    const auto p=a&0x3fffffffu;
    if(p==IosBus::PI_MASK)return mask.load();
    if(submit_host&&(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL)){auto v=B::read32(a);need(v.has_value());return *v;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){
        auto v=B::read32(a);need(v.has_value());return *v;
    }
    throw std::runtime_error("V626 unexpected MMIO read");
}
void HW_Reg_Write32(uint32_t a,uint32_t v){
    const auto p=a&0x3fffffffu;
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
    throw std::runtime_error("V626 unexpected MMIO write");
}
}
extern "C" void run_game(nw::CPUContext&);
int main()try{
    for(unsigned trial=0;trial<8;++trial){
        last_trial=trial;last_stage=last_reason=submit_stage=0;
        auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
        cause=0;mask=0xf0;
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,cause,mask);B binding(host);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        for(auto w:v626::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v626::submit_sda)c.mmu.write32(w.pc,w.word);
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
        c.pc=c.lr=W::Call;c.msr=0x8032u;c.inst_count=0;c.is_running=true;c.dispatch_saved_ctx=0;
        W w(v624::expected_client);witness=&w;
        const bool begun=w.begin(c);last_stage=w.stage();last_reason=w.failure();
        if(!begun)throw WitnessFailure{};
        // Isolated call ABI setup, NOT an execution of the OSInit caller.
        // The root and its complete linked dependency graph execute natively.
        c.pc=W::Root;c.lr=W::Return;++c.inst_count;
        const auto before_callbacks=callbacks,before_writes=control_writes;
        func_805194C4(c);
        need(c.pc==W::Return&&c.lr==W::Return&&c.is_running);
        const bool returned=w.observe(c.pc,c);last_stage=w.stage();last_reason=w.failure();
        if(!returned)throw WitnessFailure{};
        need(w.stage()==19&&w.heap_size()>0&&host.serviced_steps()==0);
        need(callbacks==before_callbacks+2&&control_writes==before_writes+1);
        const unsigned kind=1+trial%2;
        const uint32_t path=v626::paths[kind-1];
        const std::string_view name=kind==1?"/dev/stm/immediate":"/dev/stm/eventhook";
        for(unsigned i=0;i<name.size();++i)c.mmu.write8(path+i,uint8_t(name[i]));
        c.mmu.write8(path+uint32_t(name.size()),0);
        for(unsigned i=0;i<v626::vector.size();++i){
            c.mmu.write8(OpenScRoute::Source+i,v626::vector[i]);
            c.mmu.write8(OpenScRoute::Vector+i,v626::vector[i]);
        }
        c.gpr[1]-=32;c.gpr[3]=path;c.gpr[4]=0;
        c.pc=OpenRequestWitness::Open;c.lr=0x8052b090u;
        c.guest_flush_count=18000;
        OpenRequestWitness op(v639::expected_open);OpenScRoute route(v626::vector);
        open_witness=&op;sc_route=&route;open_stage=open_reason=open_polls=0;
        const bool ready=op.begin(c,kind,w.heap_size());open_stage=op.stage();open_reason=op.failure();
        if(!ready)throw WitnessFailure{};
        bool stopped=false;
        // External native tail branches unwind to the dispatcher; direct C++
        // invocation alone does not execute the allocator or caller resume.
        try{run_game(c);}catch(const OpenStop&){stopped=true;}
        need(stopped&&op.stage()==9&&op.request()&&host.serviced_steps()==0);
        need(c.pc==OpenRequestWitness::Submit&&open_vectors==trial+1&&open_returns==trial+1);
        std::cout<<"V651_OPEN_TRIAL n="<<trial<<" path="<<kind<<" request=1 serviced=0\n";
        // Continue from the exact original submit entry, retaining the
        // real allocated guest request, registers and native heap.
        open_witness=nullptr;sc_route=nullptr;
        OpenScRoute next(v626::vector,OpenScRoute::SubmitCaller);
        submit_host=&host;submit_route=&next;submit_stage=1;submit_writes=submit_polls=0;
        submit_request=op.request()&0x3fffffffu;submit_path=path&0x3fffffffu;submit_kind=kind;submit_tick=c.inst_count;
        bool acked=false;
        try{run_game(c);}catch(const SubmitStop&){acked=true;}
        need(acked&&submit_stage==8&&submit_acks==trial+1&&submit_vectors==trial+1&&host.serviced_steps()==1);
        std::cout<<"V659_SUBMIT_TRIAL n="<<trial<<" path="<<kind<<" ack=1 reply=0\n";
        submit_host=nullptr;submit_route=nullptr;witness=nullptr;
    }
    need(callbacks==16&&control_writes==8);
    std::cout<<"V627_IPC_POLLS restore=16 backward="<<loop_polls<<"\n";
    std::cout<<"V659_SUBMIT_NATIVE trials=8 heap=8 request=8 submitted=8 ack=8 reply=0 fallback=0 complete_image=0 boot_verified=0\n";
}catch(const WitnessFailure&){
    std::cout<<"V651_OPEN_FAILURE kind=witness trial="<<last_trial<<" stage="<<last_stage<<" submit_stage="<<submit_stage<<" open_stage="<<open_stage<<" open_reason="<<open_reason<<" reason="<<last_reason<<" line=0\n";return 1;
}catch(const HarnessFailure& e){
    std::cout<<"V651_OPEN_FAILURE kind=assertion trial="<<last_trial<<" stage="<<last_stage<<" submit_stage="<<submit_stage<<" open_stage="<<open_stage<<" open_reason="<<open_reason<<" reason=0 line="<<e.line<<"\n";return 1;
}catch(const std::exception& e){
    const std::string_view msg=e.what();
    const char* kind="other";
    if(msg=="V626 interpreter forbidden")kind="interpreter";
    else if(msg=="V626 unexpected syscall")kind="syscall";
    else if(msg=="V626 null branch")kind="null_branch";
    else if(msg=="V626 unexpected MMIO16"||msg=="V626 unexpected MMIO read"||msg=="V626 unexpected MMIO write")kind="mmio";
    else if(msg=="unexpected cold IPC control write"||msg=="cold IPC proof already rejected")kind="mailbox";
    std::cout<<"V651_OPEN_FAILURE kind="<<kind<<" trial="<<last_trial<<" stage="<<last_stage<<" submit_stage="<<submit_stage<<" open_stage="<<open_stage<<" open_reason="<<open_reason<<" reason=0 line=0\n";return 1;
}
