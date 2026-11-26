#pragma once
#include "wii_post_ack_ipc_join_v1229.h"
#include "wii_stm_prefix_witness_v629.h"

namespace undercover::wii {
// Continue at the authenticated IPC return, before OSInit's next instruction.
// No reset of the IOS transport, no synthetic heap or pathname installation.
class PostAckStmJoin {
public:
    explicit PostAckStmJoin(const StmPrefixExpectations& e):stm_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned stm_failure()const{return stm_.failure();}
    unsigned path_kind()const{return stm_.path_kind();}
    uint32_t heap_size()const{return heap_size_;}
    template<class C>bool begin(C& c,const PostAckIpcJoin& ipc,bool device_ok){
        const auto snap=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!device_ok||!ipc.returned_at(c)||!snap||
           !ipc.heap_size()||!stm_.begin(c,true))return fail(1);
        cpu_=&c;start_=c.inst_count;initial_=*snap;heap_size_=ipc.heap_size();stage_=1;return true;
    }
    template<class C>bool boundary(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return (stage_==1u||stage_==2u)&&!error_&&cpu_==&c&&device_ok&&
            c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            c.inst_count>=start_&&c.inst_count-start_<=8192u&&s&&same(*s,initial_);
    }
    template<class C>bool observe(C& c,uint32_t pc,bool device_ok){
        if(!boundary(c,device_ok)||!stm_.observe(pc,c))return fail(2);
        stage_=stm_.stage();if(stage_==3u)entry_tick_=c.inst_count;return true;
    }
    template<class C>bool open_at(C& c)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_==3u&&!error_&&cpu_==&c&&c.is_running&&!c.in_callback&&
            !c.dispatch_saved_ctx&&c.pc==StmPrefixWitness::Open&&
            c.inst_count==entry_tick_&&s&&same(*s,initial_);
    }
private:
    StmPrefixWitness stm_;
    const void* cpu_=nullptr;
    ColdIpcSnapshot initial_{};
    uint64_t start_=0,entry_tick_=0;
    uint32_t heap_size_=0;
    unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
};
}
