#pragma once
#include "wii_post_ack_stm_join_v1239.h"
#include "wii_open_request_witness_v639.h"

namespace undercover::wii {
// Admit only at the completed STM witness's same-context IOS_Open entry.
// Own the cache-flush SC route: unrelated syscalls cannot fall through
// to the legacy handler while this proof is active.
class PostAckOpenJoin {
public:
    PostAckOpenJoin(const OpenRequestExpectations& e,const std::array<uint8_t,28>& vector)
        :request_(e),sc_(vector){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned request_failure()const{return request_.failure();}
    uint32_t request()const{return request_.request();}
    unsigned path_kind()const{return kind_;}
    template<class C>bool begin(C& c,const PostAckStmJoin& stm,bool device_ok){
        auto snap=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!device_ok||!stm.open_at(c)||!snap||
           !request_.begin(c,stm.path_kind(),stm.heap_size()))return fail(1);
        cpu_=&c;start_=c.inst_count;initial_=*snap;kind_=stm.path_kind();stage_=1;return true;
    }
    template<class C>bool boundary(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_>=1u&&stage_<=8u&&!error_&&cpu_==&c&&device_ok&&
            c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            c.inst_count>=start_&&c.inst_count-start_<=200000u&&s&&same(*s,initial_);
    }
    template<class C>bool observe(C& c,uint32_t pc,bool device_ok){
        if(!boundary(c,device_ok)||!request_.observe(pc,c,sc_))return fail(2);
        stage_=request_.stage();if(stage_==9u)entry_tick_=c.inst_count;return true;
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
            c.inst_count==entry_tick_&&s&&same(*s,initial_)&&
            sc_.phase()==OpenScRoute::Phase::Returned;
    }
private:
    OpenRequestWitness request_;
    OpenScRoute sc_;
    const void* cpu_=nullptr;
    ColdIpcSnapshot initial_{};
    uint64_t start_=0,entry_tick_=0;
    unsigned stage_=0,error_=0,kind_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
};
}
