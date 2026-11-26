#pragma once
#include "wii_deferred_ack_execution.h"
#include "wii_external_return_v706.h"
namespace undercover::wii {
// Independent storage and active-thread contract for the next original
// dispatcher epilogue. LiveEpilogueWitness owns control-flow and RFI.
// No reply is delivered, no thread is selected by the host.
class DeferredActiveReturnJoin {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned detail()const{return detail_;}
    unsigned gqr_mismatch_mask()const{return gqr_mismatch_;}
    template<class C>bool begin(C& c,ExternalReturnWitness& frame,StmDeferredEventGate& gate,
                                IpcDeferredAckMemory& mem,uint32_t context,uint32_t wait,uint32_t counter,
                                const std::array<uint32_t,8>& interrupted_gqr,bool authenticated){
        if(stage_||error_||!authenticated||!safe(c)||(c.msr&0x8000u))return bad(1);
        if(frame.stage()!=1u||frame.source()!=HollywoodIrq::PI_HOLLYWOOD)return bad(2);
        if(!gate.completed(true)||!mem.preserved(c))return bad(3);
        if(!frame.saved_integer(c,context).ok())return bad(4);
        for(unsigned i=0;i<8;++i)if(c.gqr[i]!=interrupted_gqr[i])gqr_mismatch_|=1u<<i;
        if(gqr_mismatch_)return bad(5);
        if(!mapped(c,context,744u)||!mapped(c,wait,8u)||!mapped(c,counter,4u)||
           (context&7u)||(wait&3u)||(counter&3u))return bad(6);
        if(c.mmu.read16(context+712u)!=2u)return bad(7);
        if(c.mmu.read32(wait)||c.mmu.read32(wait+4u))return bad(8);
        if(c.mmu.read32(counter)!=1u)return bad(9);
        if(!word(c,0x800000c0u,context&0x3fffffffu)||!word(c,0x800000d4u,context)||
           !word(c,0x800000e4u,context))return bad(10);
        ctx_=context;wait_=wait;counter_=counter;frame_=&frame;gate_=&gate;mem_=&mem;cpu_=&c;
        tick_=c.inst_count;gqr_=interrupted_gqr;
        for(unsigned i=0;i<tail_.size();++i)tail_[i]=c.mmu.read32(ctx_+712u+4u*i);
        const auto s=NativeIosBinding::cold_snapshot();
        if(!s||s->steps!=5u||s->queued||s->replies||!s->event||(s->pi_cause&s->pi_mask))return bad(11);
        snapshot_=*s;stage_=1;return true;
    }
    template<class C>bool held(C& c,bool authorized){
        if(stage_!=1u||!storage(c,authorized))return false;
        if(frame_->stage()==1u)return !(c.msr&0x8000u)&&frame_->saved_integer(c,ctx_).ok();
        // The native RFI witness checks the complete restored integer
        // state. Do not require its pre-RFI saved-frame stage afterwards.
        return frame_->stage()>=2u&&frame_->stage()<=4u;
    }
    template<class C>bool finish(C& c,bool authorized){
        if(!held(c,authorized)||c.inst_count==tick_||c.gqr!=gqr_||!word(c,counter_,0u)||
           !frame_->cleared_restored(c,snapshot_.pi_cause,snapshot_.pi_mask))return fail(2);
        end_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool resumed(C& c,bool authorized){
        return stage_==2u&&storage(c,authorized)&&c.inst_count==end_&&c.gqr==gqr_&&
            word(c,counter_,0u)&&frame_->cleared_restored(c,snapshot_.pi_cause,snapshot_.pi_mask);
    }
private:
    const void* cpu_=nullptr;ExternalReturnWitness* frame_=nullptr;StmDeferredEventGate* gate_=nullptr;IpcDeferredAckMemory* mem_=nullptr;
    ColdIpcSnapshot snapshot_{};std::array<uint32_t,8> tail_{},gqr_{};
    uint32_t ctx_=0,wait_=0,counter_=0;uint64_t tick_=0,end_=0;unsigned stage_=0,error_=0,detail_=0,gqr_mismatch_=0;
    bool bad(unsigned d){if(!error_)detail_=d;return fail(1);}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||a<0x80000000u||uint64_t(a)+n>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a),q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+n-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&a.irq_mask==b.irq_mask&&
            a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    template<class C>bool storage(C& c,bool held){
        const auto s=NativeIosBinding::cold_snapshot();
        if(!held||error_||cpu_!=&c||!safe(c)||!s||!same(*s,snapshot_)||!gate_||!gate_->completed(true)||
           !mem_||!mem_->preserved(c)||!frame_||c.inst_count<tick_||c.inst_count-tick_>2048u||
           !word(c,0x800000c0u,ctx_&0x3fffffffu)||!word(c,0x800000d4u,ctx_)||!word(c,0x800000e4u,ctx_)||
           !word(c,wait_,0u)||!word(c,wait_+4u,0u)||!mapped(c,ctx_,744u)||!mapped(c,counter_,4u)||
           c.mmu.read32(counter_)>1u)return false;
        for(unsigned i=0;i<tail_.size();++i)if(c.mmu.read32(ctx_+712u+4u*i)!=tail_[i])return false;
        return true;
    }
};
}
