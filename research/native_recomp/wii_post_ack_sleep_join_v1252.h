#pragma once
#include "wii_post_ack_submit_join_v1251.h"
namespace undercover::wii {
// Follow the actual sleep function while a single IOS ACK is pending.
// Stop at SelectThread before allowing scheduler/exception dispatch.
class PostAckSleepJoin {
public:
    static constexpr uint32_t Sleep=PostAckSubmitJoin::Sleep,Select=0x80529718u,
        Thread=0x806f5318u,Current=0x800000e4u;
    explicit PostAckSleepJoin(const std::array<VectorEdge,3>& e):edges_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    uint32_t queue()const{return queue_;}
    template<class C>bool begin(C& c,const PostAckSubmitJoin& submit,bool device_ok){
        const auto s=NativeIosBinding::cold_snapshot();
        queue_=c.gpr[3];request_=submit.request();
        if(stage_||error_||!submit.ack_at(c,device_ok)||!s||
           !mapped(c,queue_,8u)||(queue_&3u)||!mapped(c,Thread,744u)||
           !equal(c,Current,Thread)||c.mmu.read16(Thread+712u)!=2u||
           c.mmu.read16(Thread+714u)!=1u||!equal(c,queue_,0)||!equal(c,queue_+4u,0)||
           !equal(c,request_,StmIos::Open))return fail(1);
        cpu_=&c;tick_=c.inst_count;sp_=c.gpr[1];lr_=c.lr;msr_=c.msr;ack_=*s;stage_=1;return true;
    }
    template<class C>bool boundary(C& c,bool device_ok)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return stage_>=1u&&stage_<=3u&&!error_&&cpu_==&c&&device_ok&&c.is_running&&
            !c.in_callback&&!c.dispatch_saved_ctx&&c.msr==msr_&&!(c.msr&0x8000u)&&
            c.inst_count>=tick_&&c.inst_count-tick_<=8192u&&s&&same(*s,ack_)&&
            equal(c,Current,Thread)&&equal(c,request_,StmIos::Open);
    }
    template<class C>bool observe(C& c,uint32_t pc,bool device_ok){
        if(!boundary(c,device_ok)||c.pc!=pc)return fail(2);
        if(stage_==1u){
            if(pc!=Sleep||c.lr!=lr_||c.gpr[1]!=sp_||c.gpr[3]!=queue_||
               c.inst_count-tick_>1u)return fail(2);
            stage_=2;return true;
        }
        if(stage_==2u){
            if(pc!=OpenRequestWitness::Disable||!edge(c,edges_[0])||c.lr!=0x8052a44cu||
               c.gpr[1]>=sp_||sp_-c.gpr[1]>256u)return fail(2);
            stage_=3;return true;
        }
        if(pc!=Select||!edge(c,edges_[1])||c.lr!=0x8052a4fcu||c.gpr[1]>=sp_||
           sp_-c.gpr[1]>256u||c.gpr[3]!=0u||!waiting(c))return fail(3);
        stage_=4;select_tick_=c.inst_count;return true;
    }
    template<class C>bool select_at(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_==4u&&!error_&&cpu_==&c&&device_ok&&c.is_running&&!c.in_callback&&
            !c.dispatch_saved_ctx&&c.pc==Select&&c.lr==edges_[1].lr&&c.inst_count==select_tick_&&
            c.msr==msr_&&s&&same(*s,ack_)&&waiting(c)&&equal(c,request_,StmIos::Open);
    }
private:
    std::array<VectorEdge,3> edges_;
    const void* cpu_=nullptr;ColdIpcSnapshot ack_{};
    unsigned stage_=0,error_=0;uint32_t queue_=0,request_=0,sp_=0,lr_=0,msr_=0;
    uint64_t tick_=0,select_tick_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool equal(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    template<class C>static bool edge(C& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4u,e.branch_word);}
    template<class C>bool waiting(C& c)const{
        return mapped(c,Thread,744u)&&c.mmu.read16(Thread+712u)==4u&&
            equal(c,Current,Thread)&&equal(c,queue_,Thread)&&equal(c,queue_+4u,Thread)&&
            equal(c,Thread+732u,queue_)&&equal(c,Thread+736u,0u)&&equal(c,Thread+740u,0u);
    }
};
}
