#pragma once
#include "wii_post_ack_stm_join_v1239.h"
#include "wii_open_request_witness_v639.h"

namespace undercover::wii {
// Admit only at the completed STM witness's same-context IOS_Open entry.
// Own the cache-flush SC route: unrelated syscalls cannot fall through
// to the legacy handler while this proof is active.
class PostAckOpenJoin {
public:
    PostAckOpenJoin(const OpenRequestExpectations& e,const std::array<uint8_t,28>& vector,unsigned first_kind=0)
        :request_(e,first_kind),sc_(vector,OpenScRoute::Caller,first_kind),epoch_(first_kind){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned request_failure()const{return request_.failure();}
    uint32_t request()const{return request_.request();}
    unsigned path_kind()const{return kind_;}
    template<class C>bool begin(C& c,const PostAckStmJoin& stm,bool device_ok){
        auto snap=NativeIosBinding::cold_snapshot();
        if(stage_||error_||epoch_.second()||!device_ok||!stm.open_at(c)||!snap||
           !request_.begin(c,stm.path_kind(),stm.heap_size()))return fail(1);
        cpu_=&c;start_=c.inst_count;initial_=*snap;kind_=stm.path_kind();stage_=1;return true;
    }
    template<class C,class Prior>bool begin_second(C& c,const Prior& prior,bool device_ok,bool held,bool descriptor,uint32_t heap_size){
        auto snap=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!epoch_.second()||!device_ok||!held||!descriptor||
           !prior.reached(c,held,descriptor)||!epoch_.admits(prior.path_kind())||!snap||!epoch_.quiet(*snap)||
           !request_.begin_second(c,prior.path_kind(),heap_size))return fail(1);
        cpu_=&c;start_=c.inst_count;initial_=*snap;kind_=prior.path_kind();stage_=1;return true;
    }
    template<class C>bool boundary(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_>=1u&&stage_<=8u&&!error_&&cpu_==&c&&device_ok&&
            c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            c.inst_count>=start_&&c.inst_count-start_<=200000u&&s&&epoch_.quiet(*s)&&same(*s,initial_);
    }
    template<class C>bool observe(C& c,uint32_t pc,bool device_ok){
        if(!boundary(c,device_ok)||!request_.observe(pc,c,sc_))return fail(2);
        stage_=request_.stage();
        if(stage_==9u){
            entry_tick_=c.inst_count;submit_lr_=c.lr;submit_sp_=c.gpr[1];
            submit_arg_=c.gpr[3];submit_msr_=c.msr;
            const auto req=request_.request();
            if(!mapped(c,req,32u))return fail(2);
            for(unsigned i=0;i<8;++i)submit_words_[i]=c.mmu.read32(req+4*i);
        }
        return true;
    }
    template<class C>bool vector_trace(C& c,uint32_t pc,bool device_ok){
        if(stage_!=7u||!boundary(c,device_ok)||sc_.phase()!=OpenScRoute::Phase::Executing)
            return fail(3);
        try{if(!sc_.vector_trace(pc,c))return fail(3);}
        catch(const std::exception&){return fail(3);}
        return true;
    }
    template<class C,class Native,class Verify>
    bool dispatch(C& c,bool device_ok,Native native,Verify verify){
        if(stage_!=7u||!boundary(c,device_ok)||sc_.phase()!=OpenScRoute::Phase::Armed)return fail(3);
        try{if(!sc_.dispatch(c,native,verify)||error_)return fail(3);}
        catch(const std::exception&){return fail(3);}
        return true;
    }
    template<class C>bool submit_at(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_==9u&&!error_&&cpu_==&c&&device_ok&&c.is_running&&!c.in_callback&&
            !c.dispatch_saved_ctx&&c.pc==OpenRequestWitness::Submit&&
            c.inst_count==entry_tick_&&c.lr==submit_lr_&&c.gpr[1]==submit_sp_&&
            c.gpr[3]==submit_arg_&&c.msr==submit_msr_&&request_unchanged(c)&&s&&epoch_.quiet(*s)&&same(*s,initial_)&&
            sc_.phase()==OpenScRoute::Phase::Returned;
    }
private:
    OpenRequestWitness request_;
    OpenScRoute sc_;
    OpenTransactionEpoch epoch_;
    const void* cpu_=nullptr;
    ColdIpcSnapshot initial_{};
    uint64_t start_=0,entry_tick_=0;
    unsigned stage_=0,error_=0,kind_=0;
    uint32_t submit_lr_=0,submit_sp_=0,submit_arg_=0,submit_msr_=0;
    std::array<uint32_t,8> submit_words_{};
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||uint64_t(a)+n>0x100000000ull)return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>bool request_unchanged(C& c)const{
        const uint32_t req=request_.request();
        if(!mapped(c,req,32u))return false;
        for(unsigned i=0;i<8;++i)if(c.mmu.read32(req+4*i)!=submit_words_[i])return false;
        const auto name=kind_==1u?std::string_view("/dev/stm/immediate"):
            kind_==2u?std::string_view("/dev/stm/eventhook"):std::string_view{};
        const auto raw=submit_words_[3];
        if(!raw||(raw&0xc0000000u)==0x40000000u||name.empty())return false;
        const uint32_t path=(raw&0x3fffffffu)|0x80000000u;
        if(!mapped(c,path,unsigned(name.size()+1u)))return false;
        for(unsigned i=0;i<name.size();++i)if(c.mmu.read8(path+i)!=uint8_t(name[i]))return false;
        return c.mmu.read8(path+uint32_t(name.size()))==0;
    }
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
};
}
