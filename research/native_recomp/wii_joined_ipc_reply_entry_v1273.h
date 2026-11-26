#pragma once
#include "wii_ipc_dispatch_v1261.h"
#include "wii_native_ios_binding.h"
#include "wii_exception_vector_witness_v457.h"
#include <algorithm>
#include <span>
namespace undercover::wii {
// Follow only the original handler prefix for a published IOS reply.
// Stop before the reply processing routine, with no guest MMIO write,
// service step, context change or wakeup admitted.
class JoinedIpcReplyEntry {
public:
    JoinedIpcReplyEntry(uint32_t handler,uint32_t read_leaf,VectorEdge reply_edge,
                        uint32_t context,uint32_t thread,std::span<const VectorEdge> edges,
                        std::span<const uint32_t> polls)
        :handler_(handler),read_leaf_(read_leaf),reply_(reply_edge),context_(context),thread_(thread),edges_(edges),polls_(polls){}
    unsigned stage()const{return stage_;}
    unsigned first_kind()const{return epoch_.first_kind();}
    unsigned failure()const{return error_;}
    unsigned reads()const{return reads_;}
    unsigned visits()const{return visits_;}
    template<class C>bool begin(C& c,IpcDispatchWitness& dispatch,ExternalReturnWitness& frame,
                                uint32_t queue,uint32_t physical,bool held){
        const auto s=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!s||!dispatch.reply_mode()||!dispatch.handler_ready(c,frame,*s,queue,held)||
           c.pc!=handler_||!physical||(physical&31u)||s->ppc!=physical||s->arm!=physical||
           reply_.pc==handler_||reply_.pc==read_leaf_||!word(c,reply_.pc,reply_.entry_word)||
           !word(c,reply_.lr-4u,reply_.branch_word)||
           std::count_if(edges_.begin(),edges_.end(),[&](auto e){
               return e.pc==reply_.pc&&e.lr==reply_.lr&&e.entry_word==reply_.entry_word&&e.branch_word==reply_.branch_word;
           })!=1)return fail(1);
        epoch_=OpenTransactionEpoch(dispatch.first_kind());
        cpu_=&c;frame_=&frame;queue_=queue;request_=physical;mail_=*s;tick_=last_=c.inst_count;
        if(!common(c,held))return fail(1);
        stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!common(c,held)||c.pc!=pc)return fail(2);
        if(!entries_){
            if(pc!=handler_||c.inst_count-tick_>1u||c.gpr[3]!=27u||c.gpr[4]!=context_)return fail(2);
            last_=c.inst_count;++entries_;return true;
        }
        if(c.inst_count!=last_||!word(c,last_pc_,last_word_)||c.lr!=last_pc_+4u)return fail(2);
        if(std::count_if(edges_.begin(),edges_.end(),[&](auto e){
            return pc==e.pc&&c.lr==e.lr&&last_word_==e.branch_word&&word(c,pc,e.entry_word);
        })!=1)return fail(2);
        if(pc==reply_.pc){
            if(c.lr!=reply_.lr||last_word_!=reply_.branch_word||!reads_||entries_<2u)return fail(3);
            stage_=2;return true;
        }
        if(pc!=read_leaf_||++entries_>16u)return fail(2);
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool guard,bool held){
        if(stage_!=1u||guard||pc==reply_.pc||!entries_||!common(c,held)||
           !word(c,pc,w)||c.inst_count-last_!=1u||++visits_>1024u)return fail(4);
        last_=c.inst_count;last_pc_=pc;last_word_=w;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!common(c,held))return fail(5);
        if(!entries_&&c.pc==handler_&&c.inst_count==tick_)return true;
        if(c.inst_count==last_&&std::find(polls_.begin(),polls_.end(),c.pc)!=polls_.end())return true;
        return fail(5);
    }
    template<class C>std::optional<uint32_t> read(C& c,uint32_t a,bool held){
        using M=IpcMailbox;using B=NativeIosBinding;
        const uint32_t p=a&0x3fffffffu;
        if(stage_!=1u||!common(c,held)||entries_<2u||
           (p!=IosBus::IPC+M::PPCCTRL&&p!=IosBus::MIRROR+M::PPCCTRL)||reads_>=16u){
            fail(6);return {};
        }
        const auto v=B::read32(a);
        if(!v||*v!=mail_.control){fail(6);return {};}
        ++reads_;return v;
    }
    bool write_refused(){return fail(7);}
    // Exact same-tick handoff at the authenticated original processor
    // entry. A later host invocation cannot re-use this observation.
    template<class C>bool processor_ready(C& c,ExternalReturnWitness& frame,uint32_t queue,
                                           uint32_t request,uint32_t processor,bool held)const{
        return stage_==2u&&common(c,held)&&frame_==&frame&&queue_==queue&&request_==request&&
            processor==reply_.pc&&c.pc==processor&&c.lr==reply_.lr&&c.inst_count==last_&&
            last_pc_==reply_.lr-4u&&last_word_==reply_.branch_word&&word(c,processor,reply_.entry_word)&&
            word(c,last_pc_,last_word_);
    }
private:
    uint32_t handler_,read_leaf_;VectorEdge reply_;
    uint32_t context_,thread_,queue_=0,request_=0,last_pc_=0,last_word_=0;
    std::span<const VectorEdge> edges_;std::span<const uint32_t> polls_;OpenTransactionEpoch epoch_{};
    const void* cpu_=nullptr;ExternalReturnWitness* frame_=nullptr;ColdIpcSnapshot mail_{};
    uint64_t tick_=0,last_=0;unsigned stage_=0,error_=0,entries_=0,reads_=0,visits_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u)&&c.mmu.read32(a)==w;
    }
    template<class C>bool common(C& c,bool held)const{
        using B=NativeIosBinding;
        const auto s=B::cold_snapshot();
        return !error_&&held&&epoch_.valid()&&(!epoch_.second()||epoch_.acknowledged_descriptors(3u-epoch_.first_kind()))&&cpu_==&c&&frame_&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            !(c.msr&0x8000u)&&c.inst_count>=tick_&&c.inst_count-tick_<=2048u&&s&&
            same_scheduler_ipc_snapshot(mail_,*s)&&frame_->pending_source(c,s->pi_cause,s->pi_mask)&&
            frame_->saved_integer(c,context_).ok()&&word(c,0x800000d4u,context_)&&
            word(c,0x800000c0u,context_&0x3fffffffu)&&c.mmu.read16(thread_+712u)==4u&&
            word(c,thread_+732u,queue_)&&word(c,queue_,thread_)&&word(c,queue_+4u,thread_)&&
            B::read_physical_word(request_)==StmIos::Reply&&B::read_physical_word(request_+4u)==epoch_.result_fd()&&
            B::read_physical_word(request_+8u)==StmIos::Open;
    }
};
}
