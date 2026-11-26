#pragma once
#include "wii_post_ack_sleep_join_v1252.h"
#include <span>
namespace undercover::wii {
// Original scheduler, stopping at the interruptible mtmsr seam. No
// external exception entry or guest context restoration is performed here.
class PostAckSchedulerJoin {
public:
    static constexpr uint32_t Select=PostAckSleepJoin::Select,Thread=PostAckSleepJoin::Thread,
        Idle=Thread+1048u,Current=PostAckSleepJoin::Current,Active=0x800000d4u,
        Physical=0x800000c0u,Get=0x80522928u,Save=0x80522934u,Set=0x805228ccu,
        Enable=0x805265c0u,Callback=0x80529128u,CallbackPtr=0x8070a908u;
    PostAckSchedulerJoin(std::span<const VectorEdge> edges,std::span<const VectorEdge> indirect,uint32_t resume,uint32_t resume_word)
        :edges_(edges),indirect_(indirect),resume_(resume),resume_word_(resume_word){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned callbacks()const{return callbacks_;}
    template<class C>bool begin(C& c,const PostAckSleepJoin& sleep,bool device_ok){
        auto s=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!sleep.select_at(c,device_ok)||!s||
           !equal(c,Active,Thread)||!equal(c,Physical,Thread&0x3fffffffu)||
           !equal(c,CallbackPtr,Callback)||!mapped(c,Idle,424u))return fail(1);
        for(unsigned i=0;i<424u;++i)if(c.mmu.read8(Idle+i))return fail(1);
        cpu_=&c;ack_=*s;queue_=sleep.queue();tick_=c.inst_count;sp_=c.gpr[1];
        r2_=c.gpr[2];r13_=c.gpr[13];stage_=1;return true;
    }
    template<class C>bool boundary(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_>=1u&&stage_<=6u&&!error_&&cpu_==&c&&device_ok&&c.is_running&&
           !c.in_callback&&!c.dispatch_saved_ctx&&c.inst_count>=tick_&&c.inst_count-tick_<=32768u&&
           (stage_==6u||!(c.msr&0x8000u))&&c.gpr[2]==r2_&&c.gpr[13]==r13_&&s&&same(*s,ack_)&&
           waiting(c)&&equal(c,CallbackPtr,Callback);
    }
    // bctrl and blr re-enter run_game. Only admit the authenticated edge
    // and its exact, single-use continuation.
    template<class C>bool indirect_poll(C& c){
        if(stage_<2u||stage_>5u)return false;
        if(c.pc==Callback)
            return !callback_return_&&callbacks_<2u&&c.ctr==Callback&&matches(c,indirect_);
        if(callback_return_&&c.pc==callback_return_&&c.lr==callback_return_&&c.ctr==Callback){
            callback_return_=0;return true;
        }
        return false;
    }
    template<class C>bool observe(C& c,uint32_t pc,bool device_ok){
        if(!boundary(c,device_ok)||c.pc!=pc||(c.msr&0x8000u))return fail(2);
        if(pc==Select){
            if(stage_!=1u||c.lr!=0x8052a4fcu||c.gpr[1]!=sp_||c.gpr[3]!=0u||c.inst_count-tick_>1u)return fail(2);
            stage_=2;return true;
        }
        if(pc==Callback){
            if(stage_<2u||stage_>5u||callbacks_>=2u||callback_return_||c.ctr!=Callback||!matches(c,indirect_))return fail(2);
            callback_return_=c.lr;++callbacks_;return true;
        }
        if(callback_return_||!matches(c,edges_))return fail(2);
        if(pc==Get&&stage_==2u&&c.lr==0x80529748u&&equal(c,Active,Thread)){
            stage_=3;return true;
        }
        if(pc==Save&&stage_==3u&&c.lr==0x80529818u&&c.gpr[3]==Thread&&
           c.gpr[1]<sp_&&sp_-c.gpr[1]<=256u){
            saved_sp_=c.gpr[1];stage_=4;return true;
        }
        if(pc==Set&&stage_==4u&&c.lr==0x80529860u&&c.gpr[3]==Idle&&
           equal(c,Active,Thread)&&saved(c)){
            stage_=5;return true;
        }
        if(pc==Enable&&stage_==5u&&c.lr==0x80529864u&&equal(c,Active,Idle)&&
           equal(c,Physical,Idle&0x3fffffffu)&&saved(c)){
            enable_msr_=c.msr;enable_sp_=c.gpr[1];enable_tick_=c.inst_count;stage_=6;return true;
        }
        return fail(3);
    }
    template<class C>bool enabled_at(C& c,bool device_ok){
        if(stage_!=6u||!boundary(c,device_ok)||c.pc!=resume_||c.lr!=0x80529864u||
           c.gpr[1]!=enable_sp_||c.msr!=(enable_msr_|0x8000u)||
           c.inst_count<=enable_tick_||c.inst_count-enable_tick_>16u||
           !equal(c,resume_-4u,resume_word_)||resume_word_>>26!=31u||((resume_word_>>1)&1023u)!=146u||
           !equal(c,Active,Idle)||!equal(c,Physical,Idle&0x3fffffffu)||!saved(c))return fail(4);
        stage_=7;return true;
    }
private:
    std::span<const VectorEdge> edges_,indirect_;
    uint32_t resume_,resume_word_;
    const void* cpu_=nullptr;ColdIpcSnapshot ack_{};
    unsigned stage_=0,error_=0,callbacks_=0;
    uint32_t queue_=0,sp_=0,r2_=0,r13_=0,saved_sp_=0,enable_msr_=0,enable_sp_=0,callback_return_=0;
    uint64_t tick_=0,enable_tick_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const uint64_t end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool equal(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==w;}
    template<class C>static bool matches(C& c,std::span<const VectorEdge> edges){
        return std::count_if(edges.begin(),edges.end(),[&](const auto& e){
            return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4u,e.branch_word);
        })==1;
    }
    template<class C>bool waiting(C& c)const{
        return mapped(c,Thread,744u)&&c.mmu.read16(Thread+712u)==4u&&
            equal(c,queue_,Thread)&&equal(c,queue_+4u,Thread)&&equal(c,Thread+732u,queue_)&&
            equal(c,Thread+736u,0u)&&equal(c,Thread+740u,0u);
    }
    template<class C>bool saved(C& c)const{
        return saved_sp_&&equal(c,Thread+4u,saved_sp_)&&equal(c,Thread+408u,0x80529818u);
    }
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
};
}
