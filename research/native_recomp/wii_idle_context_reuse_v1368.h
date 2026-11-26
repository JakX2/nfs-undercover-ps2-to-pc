#pragma once
#include "wii_post_ack_sleep_join_v1252.h"
namespace undercover::wii {
// Read-only provenance for the inactive, previously used OSContext.
// Capture at the completed second ACK, before original OSSleepThread.
// No zeroing, context replacement or synthetic thread transition.
class IdleContextReuse {
public:
    static constexpr uint32_t Thread=PostAckSleepJoin::Thread,Idle=Thread+1048u;
    template<class C>bool capture(C& c,const PostAckSubmitJoin& submit,bool held){
        const auto s=NativeIosBinding::cold_snapshot();
        if(cpu_||!held||!submit.ack_at(c,held)||!s||s->steps!=3u||
           !active_thread(c)||!mapped(c,Idle,0x2c8u)||c.mmu.read32(Idle+0x1a0u)!=0u)return false;
        for(unsigned i=0;i<image_.size();++i)image_[i]=c.mmu.read8(Idle+i);
        cpu_=&c;tick_=c.inst_count;request_=submit.request();return true;
    }
    template<class C>bool preserved(C& c,bool held)const{
        return scheduler_detail(c,held,false)==0u;
    }
    // A native SelectThread transition can remove the current-thread
    // pointer after saving the waiting thread but before setting idle.
    // The active OSContext and its physical alias must still be the
    // previous thread, and the inactive idle image remains exact.
    template<class C>unsigned scheduler_detail(C& c,bool held,bool saved)const{
        if(!cpu_||cpu_!=&c||!held||!c.is_running||c.in_callback||c.dispatch_saved_ctx||
           c.inst_count<tick_||c.inst_count-tick_>8192u)return 1u;
        if(!word(c,0x800000d4u,Thread)||!word(c,0x800000c0u,Thread&0x3fffffffu))return 2u;
        if(!word(c,0x800000e4u,Thread)&&!(saved&&word(c,0x800000e4u,0u)))return 3u;
        if(!mapped(c,Idle,0x2c8u))return 4u;
        for(unsigned i=0;i<image_.size();++i)if(c.mmu.read8(Idle+i)!=image_[i])return 5u;
        return 0u;
    }
    template<class C>bool select_at(C& c,const PostAckSleepJoin& sleep,bool held)const{
        const auto s=NativeIosBinding::cold_snapshot();
        return preserved(c,held)&&sleep.select_at(c,held)&&s&&s->steps==3u&&
               s->ppc==(request_&0x3fffffffu);
    }
private:
    const void* cpu_=nullptr;uint64_t tick_=0;uint32_t request_=0;
    std::array<uint8_t,0x2c8u> image_{};
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||a<0x80000000u||uint64_t(a)+n>0x81800000ull)return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t v){return mapped(c,a,4u)&&c.mmu.read32(a)==v;}
    template<class C>static bool active_thread(C& c){
        return word(c,0x800000d4u,Thread)&&word(c,0x800000c0u,Thread&0x3fffffffu)&&word(c,0x800000e4u,Thread);
    }
};
}
