#pragma once
#include "wii_external_return_v706.h"
#include "wii_scheduler_irq_entry_v1259.h"
#include "wii_si_dispatch_v667.h"
#include "wii_stm_deferred_event_gate.h"
namespace undercover::wii {
struct IpcDispatchExpectations {
    SiDispatchExpectations code;
    uint32_t handler,context,thread,table,irq_global,counter;
};
// Bounded original dispatcher prefix. The IRQ source is the actual pending
// native IOS ACK or reply, not the earlier SI transfer. Never service or acknowledge it.
class IpcDispatchWitness {
public:
    explicit IpcDispatchWitness(IpcDispatchExpectations e,unsigned first_kind=0):e_(e),epoch_(first_kind){}
    unsigned first_kind()const{return epoch_.first_kind();}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned detail()const{return detail_;}
    unsigned visits()const{return visits_;}
    unsigned cause_reads()const{return cause_reads_;}
    unsigned mask_reads()const{return mask_reads_;}
    template<class C>bool begin(C& c,ExternalReturnWitness& frame,const ColdIpcSnapshot& s,
                                uint32_t queue,bool held){
        return begin_impl(c,frame,s,queue,held,0u);
    }
    // Explicit second-interrupt lane. The same original dispatcher is
    // admitted only for the published response to the original request.
    template<class C>bool begin_reply(C& c,ExternalReturnWitness& frame,const ColdIpcSnapshot& s,
                                     uint32_t queue,uint32_t physical_request,bool held){
        if(!physical_request)return fail(1);
        return begin_impl(c,frame,s,queue,held,physical_request);
    }
    // The third startup IRQ interrupts the selected active caller. It
    // has a pending deferred event, not a synchronous reply or waiter.
    template<class C>bool begin_deferred(C& c,ExternalReturnWitness& frame,const ColdIpcSnapshot& s,
                                         uint32_t empty_queue,uint32_t request,StmDeferredEventGate& gate,bool held){
        if(stage_||error_||!epoch_.second()||!request||!gate.deferred_held(held))return fail(1);
        deferred_request_=request;deferred_gate_=&gate;
        return begin_impl(c,frame,s,empty_queue,held,0u);
    }
    bool reply_mode()const{return stage_&&!error_&&reply_request_!=0;}
    bool deferred_mode()const{return stage_&&!error_&&deferred_request_!=0;}
private:
    template<class C>bool begin_impl(C& c,ExternalReturnWitness& frame,const ColdIpcSnapshot& s,
                                     uint32_t queue,bool held,uint32_t physical_request){
        using M=IpcMailbox;using H=HollywoodIrq;
        if(stage_||error_||!held||!safe(c)||!epoch_held()||c.pc!=SiDispatchWitness::Dispatcher||
           c.gpr[3]!=4u||c.gpr[4]!=e_.context||frame.source()!=H::PI_HOLLYWOOD||
           !frame.pending_source(c,s.pi_cause,s.pi_mask)||!frame.saved_integer(c,e_.context).ok()||
           !(s.flags&H::IPC_PPC)||s.queued||
           (deferred_request_?!deferred_wire(c,s):s.event||
            (physical_request?!reply_wire(c,s,physical_request):
             (!(s.control&M::Y2)||(s.control&(M::Y1|M::X1))||s.steps!=epoch_.ack_steps()||s.replies!=1u)))||
           !word(c,c.pc,e_.code.dispatcher_word)||!mapped(c,e_.counter,4u))return fail(1);
        reply_request_=physical_request;queue_=queue;cpu_=&c;frame_=&frame;s_=s;counter_=c.mmu.read32(e_.counter);
        if(counter_==0xffffffffu||!tables(c))return fail(1);
        start_=last_=last_entry_=c.inst_count;stage_=1;return true;
    }
public:
    bool read(uint32_t a,uint32_t value){
        if(stage_<1u||stage_>5u||error_)return fail(2);
        const auto p=a&0x3fffffffu;
        if(p==IosBus::PI_CAUSE&&value==s_.pi_cause&&cause_reads_<16u){++cause_reads_;return true;}
        if(p==IosBus::PI_MASK&&value==s_.pi_mask&&mask_reads_<16u){++mask_reads_;return true;}
        return fail(2);
    }
    template<class C>bool poll(C& c,const ColdIpcSnapshot& s,bool held){
        if(!common(c,s,held)||c.inst_count<last_||c.inst_count-last_>1u)return fail(3);
        last_=c.inst_count;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool guard,const ColdIpcSnapshot& s,bool held){
        if(guard)return fail_detail(4,1);
        if(const auto d=common_detail(c,s,held))return fail_detail(4,d);
        if(!word(c,pc,w))return fail_detail(4,7);
        if(c.inst_count-last_!=1u)return fail_detail(4,8);
        if(++visits_>2048u)return fail_detail(4,9);
        last_=c.inst_count;return true;
    }
    template<class C>bool observe(C& c,uint32_t pc,const ColdIpcSnapshot& s,bool held){
        if(!common(c,s,held)||c.pc!=pc||c.inst_count<=last_entry_||c.inst_count<last_||c.inst_count-last_>1u)return fail(5);
        if(stage_<=4u){
            const auto& e=e_.code.edges[stage_-1u];
            if(pc!=e.pc||c.lr!=e.lr||!word(c,pc,e.entry_word)||!word(c,c.lr-4u,e.branch_word))return fail(5);
        }else if(pc!=e_.handler||c.gpr[3]!=27u||c.gpr[4]!=e_.context||c.ctr!=pc||
                 c.lr!=e_.code.indirect_pc+4u||!word(c,pc,e_.code.handler_word)||
                 !word(c,e_.code.indirect_pc,e_.code.indirect_word)||!cause_reads_||!mask_reads_||
                 !word(c,e_.counter,counter_+1u))return fail(6);
        last_=last_entry_=c.inst_count;++stage_;return true;
    }
    // Transfer the admitted handler entry to a follow-on witness only on
    // the very same CPU, saved frame, queue and observation tick.
    template<class C>bool handler_ready(C& c,ExternalReturnWitness& frame,const ColdIpcSnapshot& s,uint32_t queue,bool held)const{
        return stage_==6u&&!error_&&held&&epoch_held()&&cpu_==&c&&frame_==&frame&&queue_==queue&&safe(c)&&
            c.inst_count==last_entry_&&same_scheduler_ipc_snapshot(s_,s)&&frame.pending_source(c,s.pi_cause,s.pi_mask)&&
            frame.saved_integer(c,e_.context).ok()&&tables(c)&&(!reply_request_||reply_wire(c,s,reply_request_))&&
            (!deferred_request_||deferred_wire(c,s))&&
            c.pc==e_.handler&&c.ctr==e_.handler&&
            c.gpr[3]==27u&&c.gpr[4]==e_.context&&c.lr==e_.code.indirect_pc+4u&&
            word(c,c.pc,e_.code.handler_word)&&word(c,e_.code.indirect_pc,e_.code.indirect_word)&&
            word(c,e_.counter,counter_+1u);
    }
private:
    IpcDispatchExpectations e_;OpenTransactionEpoch epoch_;const void* cpu_=nullptr;ExternalReturnWitness* frame_=nullptr;
    ColdIpcSnapshot s_{};uint32_t queue_=0,counter_=0,reply_request_=0,deferred_request_=0;
    StmDeferredEventGate* deferred_gate_=nullptr;
    uint64_t start_=0,last_=0,last_entry_=0;unsigned stage_=0,error_=0,visits_=0,cause_reads_=0,mask_reads_=0;
    unsigned detail_=0;
    bool fail_detail(unsigned n,unsigned d){if(!error_)detail_=d;return fail(n);}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const auto end=uint64_t(a)+n;
        return n&&((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull))&&
            c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    bool epoch_held()const{return epoch_.valid()&&(!epoch_.second()||epoch_.acknowledged_descriptors(3u-epoch_.first_kind()));}
    template<class C>bool reply_wire(C& c,const ColdIpcSnapshot& s,uint32_t request)const{
        using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
        if(!request||(request&31u)||request>0x13ffffc0u||s.ppc!=request||s.arm!=request||
           (s.control&(M::X1|M::Y1|M::Y2))!=M::Y1||!(s.control&M::IY1)||
           !(s.flags&H::IPC_PPC)||!(s.irq_mask&H::IPC_PPC)||
           s.steps!=epoch_.reply_steps()||s.replies||s.queued||s.event)return false;
        const uint32_t a=request|0x80000000u;
        return mapped(c,a,64u)&&word(c,a,S::Reply)&&word(c,a+4u,epoch_.result_fd())&&word(c,a+8u,S::Open);
    }
    template<class C>bool deferred_wire(C& c,const ColdIpcSnapshot& s)const{
        using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
        if(!deferred_gate_||!deferred_gate_->deferred_held(true)||!deferred_request_||
           (deferred_request_&31u)||deferred_request_>0x13ffffc0u||s.ppc!=deferred_request_||
           (s.control&(M::X1|M::Y1|M::Y2))!=M::Y2||!(s.control&M::IY2)||
           !(s.flags&H::IPC_PPC)||!(s.irq_mask&H::IPC_PPC)||s.steps!=5u||s.replies||s.queued||!s.event)return false;
        const uint32_t a=deferred_request_|0x80000000u;
        return mapped(c,a,64u)&&word(c,a,S::Ioctl)&&word(c,a+8u,epoch_.first_kind()==2u?0u:1u)&&
            word(c,a+12u,S::EventHook);
    }
    template<class C>bool tables(C& c)const{
        if(!mapped(c,e_.thread+712u,2u)||!word(c,0x800000d4u,e_.context)||
           !word(c,0x800000c0u,e_.context&0x3fffffffu)||!word(c,e_.irq_global,e_.table)||
           !word(c,e_.table+4u*27u,e_.handler))return false;
        if(deferred_request_)
            return e_.context==e_.thread&&word(c,0x800000e4u,e_.thread)&&c.mmu.read16(e_.thread+712u)==2u&&
                word(c,queue_,0u)&&word(c,queue_+4u,0u)&&word(c,e_.thread+736u,0u)&&word(c,e_.thread+740u,0u);
        return c.mmu.read16(e_.thread+712u)==4u&&word(c,queue_,e_.thread)&&
            word(c,queue_+4u,e_.thread)&&word(c,e_.thread+732u,queue_);
    }
    template<class C>bool common(C& c,const ColdIpcSnapshot& s,bool held)const{
        return !common_detail(c,s,held);
    }
    template<class C>unsigned common_detail(C& c,const ColdIpcSnapshot& s,bool held)const{
        if(stage_<1u||stage_>5u||error_||!held||cpu_!=&c||!safe(c)||
           c.inst_count<start_||c.inst_count-start_>8192u)return 2;
        if(!epoch_held()||!same_scheduler_ipc_snapshot(s_,s))return 3;
        if(!frame_||!frame_->pending_source(c,s.pi_cause,s.pi_mask))return 4;
        if(!frame_->saved_integer(c,e_.context).ok())return 5;
        if(!tables(c))return 6;
        if(reply_request_&&!reply_wire(c,s,reply_request_))return 10;
        if(deferred_request_&&!deferred_wire(c,s))return 10;
        return 0;
    }
};
}
