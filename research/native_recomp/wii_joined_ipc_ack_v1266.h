#pragma once
#include "wii_cold_open_reply_gate_v1253.h"
#include "wii_external_return_v706.h"
#include "wii_ipc_dispatch_v1261.h"
#include "wii_exception_vector_witness_v457.h"
#include <algorithm>
#include <span>
namespace undercover::wii {
// Same live CPU, saved idle context, waiting thread and native transport.
// No synthesized handler call, ACK write or guest return.
class JoinedIpcAck {
public:
    JoinedIpcAck(uint32_t handler,uint32_t returned,uint32_t return_word,uint32_t final_blr,uint32_t context,
                 uint32_t thread,std::span<const VectorEdge> edges,std::span<const uint32_t> polls,unsigned first_kind=0)
        :handler_(handler),returned_(returned),word_(return_word),final_blr_(final_blr),context_(context),thread_(thread),edges_(edges),polls_(polls),gate_(first_kind){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned reads()const{return reads_;}
    unsigned gate_stage()const{return gate_.stage();}
    unsigned gate_failure()const{return gate_.failure();}
    template<class C>bool begin(C& c,IpcDispatchWitness& dispatch,ExternalReturnWitness& frame,
                                uint32_t queue,uint32_t physical,unsigned kind,bool held){
        const auto snapshot=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!snapshot||!dispatch.handler_ready(c,frame,*snapshot,queue,held)||c.pc!=handler_||
           c.lr!=returned_||c.ctr!=handler_||c.gpr[3]!=27u||c.gpr[4]!=context_||
           !equal(c,returned_,word_)||!equal(c,returned_-4u,0x4e800421u)||!equal(c,final_blr_,0x4e800020u))return fail(1);
        cpu_=&c;frame_=&frame;queue_=queue;gp_=c.gpr;msr_=c.msr;tick_=last_=c.inst_count;
        if(!common(c,held)||!gate_.begin(physical,kind,true))return fail(1);
        stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!boundary(c,held)||pc!=c.pc)return fail(2);
        if(!entries_){
            if(pc!=handler_||c.lr!=returned_||c.gpr[3]!=27u||c.gpr[4]!=context_||
               c.inst_count-tick_>1u)return fail(2);
            last_=c.inst_count;
        }else{
            if(pc!=0x8051905cu&&pc!=0x8051906cu&&pc!=0x8051b060u)return fail(2);
            if(std::count_if(edges_.begin(),edges_.end(),[&](auto e){
                return pc==e.pc&&c.lr==e.lr&&equal(c,pc,e.entry_word)&&equal(c,c.lr-4u,e.branch_word);
            })!=1)return fail(2);
        }
        if(++entries_>32u)return fail(2);
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool guard,bool held){
        if(guard||!entries_||!boundary(c,held)||!equal(c,pc,w)||c.inst_count-last_!=1u||
           ++visits_>8192u)return fail(3);
        last_=c.inst_count;last_pc_=pc;last_word_=w;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!boundary(c,held))return fail(4);
        if(c.pc==handler_&&!entries_&&c.inst_count==tick_)return true;
        if(c.pc==returned_&&entries_&&gate_.stage()==3u)return true;
        if(std::find(polls_.begin(),polls_.end(),c.pc)!=polls_.end())return true;
        return fail(4);
    }
    template<class C>std::optional<uint32_t> read(C& c,uint32_t a,bool held){
        using B=NativeIosBinding;using M=IpcMailbox;using H=HollywoodIrq;
        const auto p=a&0x3fffffffu;
        if(!boundary(c,held)||++reads_>32u||
           (p!=IosBus::IPC+M::PPCCTRL&&p!=IosBus::MIRROR+M::PPCCTRL&&
            p!=IosBus::IPC+H::PPC_FLAG&&p!=IosBus::MIRROR+H::PPC_FLAG)){fail(5);return {};}
        const auto v=B::read32(a);if(!v)fail(5);return v;
    }
    template<class C>bool write(C& c,uint32_t a,uint32_t value,bool held){
        if(!boundary(c,held)||!gate_.write(a,value,c.msr,true))return fail(6);
        return true;
    }
    template<class C>bool finish(C& c,bool held){
        if(!boundary(c,held)||gate_.stage()!=3u||!reads_||!visits_||entries_<2u||
           c.pc!=returned_||c.lr!=returned_||!equal(c,returned_,word_)||
           last_pc_!=final_blr_||last_word_!=0x4e800020u||c.inst_count!=last_||
           c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.msr!=msr_)return fail(7);
        for(unsigned i=13;i<32u;++i)if(c.gpr[i]!=gp_[i])return fail(7);
        stage_=2;return true;
    }
    template<class C>bool publish(C& c,bool held){
        if(stage_!=2u||error_||!common(c,held)||c.pc!=returned_||
           !gate_.publish(c.msr,true)||!gate_.reply_pending(true)||!common(c,held))return fail(8);
        stage_=3;return true;
    }
private:
    uint32_t handler_,returned_,word_,final_blr_,context_,thread_,queue_=0,msr_=0,last_pc_=0,last_word_=0;
    std::span<const VectorEdge> edges_;std::span<const uint32_t> polls_;
    const void* cpu_=nullptr;ExternalReturnWitness* frame_=nullptr;ColdOpenReplyGate gate_;
    std::array<uint32_t,32> gp_{};
    uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0,entries_=0,visits_=0,reads_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool equal(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>bool common(C& c,bool held)const{
        return held&&cpu_==&c&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&c.msr==msr_&&!(c.msr&0x8000u)&&
            c.inst_count>=tick_&&c.inst_count-tick_<=8192u&&frame_&&frame_->saved_integer(c,context_).ok()&&
            equal(c,0x800000d4u,context_)&&equal(c,0x800000c0u,context_&0x3fffffffu)&&
            c.mmu.read16(thread_+712u)==4u&&equal(c,thread_+732u,queue_)&&
            equal(c,queue_,thread_)&&equal(c,queue_+4u,thread_);
    }
    template<class C>bool boundary(C& c,bool held)const{
        return stage_==1u&&!error_&&common(c,held)&&gate_.boundary(true);
    }
};
}
